from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from medrix_flow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from medrix_flow.runtime.utils import now_iso

from .adapters import AcademicSourceAdapter, build_default_adapters
from .formatters import format_apa7_reference, format_bibtex_entry
from .queries import build_query_expansions
from .quality import (
    canonical_reason,
    hydrate_quality_metadata,
    preprint_ratio,
    provider_breakdown,
    venue_breakdown,
    version_priority_score,
)
from .ranking import score_papers, select_core_papers
from .repository import AcademicRepository
from .types import (
    AcademicGraph,
    EvidenceCardRecord,
    IngestResult,
    OutlineNodeRecord,
    PaperEdgeRecord,
    PaperRecord,
    ReferenceEntry,
    ReportExportRecord,
    ResearchProject,
    SearchQueryRecord,
    SynthesisResult,
)
from .utils import (
    detect_domain,
    merge_unique,
    normalize_doi,
    normalize_title_key,
    slugify,
    summarize_abstract,
    today_stamp,
    topic_terms,
)

logger = logging.getLogger(__name__)


class AcademicResearchService:
    def __init__(
        self,
        repository: AcademicRepository,
        *,
        adapters: list[AcademicSourceAdapter] | None = None,
    ) -> None:
        self._repository = repository
        self._adapters = adapters or []

    async def create_project(
        self,
        *,
        thread_id: str,
        topic: str,
        scope: str | None = None,
        metadata: dict[str, Any] | None = None,
        force_new: bool = False,
    ) -> ResearchProject:
        topic_key = normalize_title_key(topic)
        domain = detect_domain(topic, scope)
        if not force_new:
            existing = await self._repository.find_project_by_thread_topic(thread_id, topic_key)
            if existing is not None:
                return existing

        if force_new:
            topic_key = f"{topic_key}:{uuid.uuid4().hex[:8]}"

        project = await self._repository.create_project(
            project_id=str(uuid.uuid4()),
            thread_id=thread_id,
            topic=topic.strip(),
            topic_key=topic_key,
            scope=scope.strip() if scope else None,
            status="created",
            domain=domain,
            metadata=metadata or {},
        )
        return project

    async def ingest_project(
        self,
        project_id: str,
        *,
        max_candidates: int = 120,
        core_paper_limit: int = 24,
        use_local_uploads: bool = True,
        source_profile: str | None = None,
        quality_mode: str | None = None,
        preprint_policy: str | None = None,
    ) -> IngestResult:
        project = await self._require_project(project_id)
        queries = build_query_expansions(project)
        await self._repository.replace_search_queries(project.project_id, queries)

        resolved_source_profile = source_profile or ("cs_ai_premium" if project.domain == "cs_ai" else "default")
        resolved_quality_mode = quality_mode or ("strict" if project.domain == "cs_ai" else "balanced")
        resolved_preprint_policy = preprint_policy or "prefer_final"

        configured_adapters = self._adapters or list(
            build_default_adapters(
                project.domain,
                topic=project.topic,
                scope=project.scope,
                source_profile=resolved_source_profile,
            )
        )
        terms = topic_terms(project.topic, project.scope)

        local_papers = await self._load_local_upload_papers(project) if use_local_uploads else []
        provider_limit = max(4, min(12, max_candidates // max(len(queries), 1)))
        raw_papers: list[PaperRecord] = list(local_papers)

        for adapter in configured_adapters:
            if len(raw_papers) >= max_candidates:
                break
            query_window = self._query_window_for_adapter(adapter.name)
            for query in queries[:query_window]:
                if len(raw_papers) >= max_candidates:
                    break
                try:
                    results = await adapter.search(
                        query.query_text,
                        project_id=project.project_id,
                        limit=min(provider_limit, max_candidates - len(raw_papers)),
                    )
                except Exception:
                    logger.warning("Academic adapter failed: %s", adapter.name, exc_info=True)
                    continue
                raw_papers.extend(results)
                if adapter.name == "arxiv":
                    break

        normalized_papers = [hydrate_quality_metadata(paper.model_copy(deep=True)) for paper in raw_papers]
        merged = self._dedupe_candidates(
            normalized_papers,
            quality_mode=resolved_quality_mode,
            preprint_policy=resolved_preprint_policy,
        )
        scored = score_papers(list(merged.values()), terms=terms, quality_mode=resolved_quality_mode)
        stored = await self._repository.upsert_papers(project.project_id, scored)
        selected = select_core_papers(stored, limit=max(20, min(core_paper_limit, 40)))
        references = self._build_references(stored)

        await self._repository.update_project_status(
            project.project_id,
            status="ingested",
            metadata={
                "raw_candidate_count": len(raw_papers),
                "paper_count": len(stored),
                "query_count": len(queries),
                "core_paper_limit": max(20, min(core_paper_limit, 40)),
                "source_profile": resolved_source_profile,
                "quality_mode": resolved_quality_mode,
                "preprint_policy": resolved_preprint_policy,
                "provider_breakdown": provider_breakdown(stored),
                "venue_breakdown": venue_breakdown(stored),
                "preprint_ratio": preprint_ratio(stored),
                "canonical_reference_count": len([entry for entry in references if entry.included_in_final]),
                "last_ingested_at": now_iso(),
            },
            domain=project.domain,
        )
        updated_project = await self._require_project(project.project_id)
        return IngestResult(
            project=updated_project,
            queries=queries,
            raw_candidate_count=len(raw_papers),
            paper_count=len(stored),
            selected_papers=selected,
            provider_breakdown=provider_breakdown(stored),
            venue_breakdown=venue_breakdown(stored),
            preprint_ratio=preprint_ratio(stored),
            canonical_reference_count=len([entry for entry in references if entry.included_in_final]),
        )

    async def synthesize_project(
        self,
        project_id: str,
        *,
        output_dir: Path | None = None,
        include_graph: bool = False,
    ) -> SynthesisResult:
        project = await self._require_project(project_id)
        papers = await self._repository.list_project_papers(project.project_id)
        if not papers:
            raise ValueError(f"Project {project_id} has no papers. Run ingest first.")

        core_papers = self._core_papers_for_synthesis(project, papers)
        outline = self._build_outline(project, core_papers)
        evidence_cards = self._build_evidence_cards(project, core_papers, outline)
        edges = self._build_graph_edges(project, core_papers, evidence_cards, outline)
        references = self._build_references(papers)
        graph = await self._persist_graph_bundle(project, outline, evidence_cards, edges)

        export_paths: list[Path] = []
        if output_dir is not None:
            export_paths = await self._write_exports(
                project=project,
                output_dir=output_dir,
                all_papers=papers,
                core_papers=core_papers,
                outline=outline,
                evidence_cards=evidence_cards,
                references=references,
                graph=graph if include_graph else None,
            )
            virtual_exports = [self._to_virtual_output(project.thread_id, path) for path in export_paths]
            await self._repository.replace_report_exports(
                project.project_id,
                [
                    ReportExportRecord(
                        export_id=str(uuid.uuid4()),
                        project_id=project.project_id,
                        export_kind=path.suffix.lstrip(".") or path.name,
                        path=virtual_path,
                        summary={
                            "project_id": project.project_id,
                            "reference_count": len([entry for entry in references if entry.included_in_final]),
                            "evidence_count": len(evidence_cards),
                            "reference_mix": provider_breakdown(papers),
                            "preprint_ratio": preprint_ratio(papers),
                            "top_venues": venue_breakdown(papers),
                        },
                        created_at=now_iso(),
                    )
                    for path, virtual_path in zip(export_paths, virtual_exports, strict=True)
                ],
            )
        await self._repository.update_project_status(
            project.project_id,
            status="synthesized",
            metadata={
                "outline_count": len(outline),
                "evidence_count": len(evidence_cards),
                "reference_count": len([entry for entry in references if entry.included_in_final]),
                "last_synthesized_at": now_iso(),
            },
        )
        updated_project = await self._require_project(project.project_id)
        return SynthesisResult(
            project=updated_project,
            outline=outline,
            evidence_cards=evidence_cards,
            references=references,
            graph=graph,
            export_files=[str(path) for path in export_paths],
        )

    async def run_research(
        self,
        *,
        thread_id: str,
        topic: str,
        scope: str | None = None,
        output_dir: Path | None = None,
        include_graph: bool = False,
        max_candidates: int = 120,
        core_paper_limit: int = 24,
        source_profile: str | None = None,
        quality_mode: str | None = None,
        preprint_policy: str | None = None,
    ) -> SynthesisResult:
        project = await self.create_project(thread_id=thread_id, topic=topic, scope=scope)
        await self.ingest_project(
            project.project_id,
            max_candidates=max_candidates,
            core_paper_limit=core_paper_limit,
            source_profile=source_profile,
            quality_mode=quality_mode,
            preprint_policy=preprint_policy,
        )
        return await self.synthesize_project(
            project.project_id,
            output_dir=output_dir,
            include_graph=include_graph,
        )

    async def get_project_summary(self, project_id: str) -> dict[str, Any]:
        project = await self._require_project(project_id)
        papers = await self._repository.list_project_papers(project.project_id)
        outline = await self._repository.list_outline_nodes(project.project_id)
        evidence = await self._repository.list_evidence_cards(project.project_id)
        exports = await self._repository.list_report_exports(project.project_id)
        references = self._build_references(papers)
        return {
            "project": project.model_dump(),
            "paper_count": len(papers),
            "reference_count": len([entry for entry in references if entry.included_in_final]),
            "evidence_count": len(evidence),
            "outline_count": len(outline),
            "export_files": [item.path for item in exports],
            "provider_breakdown": provider_breakdown(papers),
            "venue_breakdown": venue_breakdown(papers),
            "preprint_ratio": preprint_ratio(papers),
            "canonical_reference_count": len([entry for entry in references if entry.included_in_final]),
        }

    async def get_references(self, project_id: str) -> list[ReferenceEntry]:
        project = await self._require_project(project_id)
        papers = await self._repository.list_project_papers(project.project_id)
        return self._build_references(papers)

    async def get_graph(self, project_id: str) -> AcademicGraph:
        await self._require_project(project_id)
        return await self._repository.get_graph(project_id)

    def thread_outputs_dir(self, thread_id: str) -> Path:
        return get_paths().sandbox_outputs_dir(thread_id)

    async def _persist_graph_bundle(
        self,
        project: ResearchProject,
        outline: list[OutlineNodeRecord],
        evidence_cards: list[EvidenceCardRecord],
        edges: list[PaperEdgeRecord],
    ) -> AcademicGraph:
        await self._repository.replace_outline_nodes(project.project_id, outline)
        await self._repository.replace_evidence_cards(project.project_id, evidence_cards)
        await self._repository.replace_paper_edges(project.project_id, edges)
        return await self._repository.get_graph(project.project_id)

    def _dedupe_candidates(
        self,
        papers: list[PaperRecord],
        *,
        quality_mode: str,
        preprint_policy: str,
    ) -> dict[str, PaperRecord]:
        deduped: dict[str, PaperRecord] = {}
        for paper in papers:
            existing = deduped.get(paper.canonical_id)
            if existing is None:
                deduped[paper.canonical_id] = paper
                continue

            preferred, alternate = self._preferred_and_alternate_version(
                existing,
                paper,
                quality_mode=quality_mode,
                preprint_policy=preprint_policy,
            )
            merged = preferred.model_copy(deep=True)
            merged.provider = preferred.provider
            merged.provider_id = preferred.provider_id
            merged.source_url = preferred.source_url or alternate.source_url
            merged.oa_url = preferred.oa_url or alternate.oa_url
            merged.canonical_source = preferred.canonical_source
            merged.quality_signals = {**alternate.quality_signals, **preferred.quality_signals}
            merged.abstract = merged.abstract or paper.abstract
            merged.venue = merged.venue or paper.venue
            merged.year = merged.year or paper.year
            merged.doi = merged.doi or paper.doi
            merged.pmid = merged.pmid or paper.pmid
            merged.pmcid = merged.pmcid or paper.pmcid
            merged.arxiv_id = merged.arxiv_id or paper.arxiv_id
            merged.cited_by_count = max(existing.cited_by_count or 0, paper.cited_by_count or 0) or None
            merged.authors = existing.authors or paper.authors
            merged.keywords = merge_unique(existing.keywords + paper.keywords)
            merged.methods = merge_unique(existing.methods + paper.methods)
            merged.populations = merge_unique(existing.populations + paper.populations)
            merged.conflict_flags = merge_unique(existing.conflict_flags + paper.conflict_flags)
            merged.raw_source = {**alternate.raw_source, **preferred.raw_source}
            merged.metadata_only = existing.metadata_only and paper.metadata_only
            if paper.provider == "local-upload":
                merged.provider = paper.provider
                merged.canonical_source = paper.canonical_source
            merged = hydrate_quality_metadata(merged)
            deduped[paper.canonical_id] = merged
        return deduped

    @staticmethod
    def _preferred_and_alternate_version(
        existing: PaperRecord,
        incoming: PaperRecord,
        *,
        quality_mode: str,
        preprint_policy: str,
    ) -> tuple[PaperRecord, PaperRecord]:
        existing_score = version_priority_score(existing, quality_mode=quality_mode, preprint_policy=preprint_policy)
        incoming_score = version_priority_score(incoming, quality_mode=quality_mode, preprint_policy=preprint_policy)
        if incoming_score > existing_score:
            return incoming, existing
        return existing, incoming

    async def _load_local_upload_papers(self, project: ResearchProject) -> list[PaperRecord]:
        uploads_dir = get_paths().sandbox_uploads_dir(project.thread_id)
        if not uploads_dir.exists():
            return []

        papers: list[PaperRecord] = []
        markdown_files = sorted(
            [
                path
                for path in uploads_dir.iterdir()
                if path.is_file() and path.suffix.lower() == ".md"
            ]
        )
        for path in markdown_files:
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue
            title = self._extract_local_title(path, content)
            doi = self._extract_doi(content)
            year = self._extract_year(content)
            summary = summarize_abstract(content, limit=800)
            papers.append(
                PaperRecord(
                    paper_id=f"{project.project_id}:local-upload:{slugify(path.stem, fallback='upload')}",
                    project_id=project.project_id,
                    canonical_id=f"local:{normalize_doi(doi) or normalize_title_key(title)}",
                    title=title,
                    authors=[],
                    year=year,
                    venue="User uploaded document",
                    abstract=summary,
                    doi=normalize_doi(doi),
                    provider="local-upload",
                    provider_id=path.name,
                    source_url=f"/api/threads/{project.thread_id}/artifacts/mnt/user-data/uploads/{path.name}",
                    oa_url=None,
                    metadata_only=False,
                    keywords=[],
                    methods=[],
                    populations=[],
                    conflict_flags=[],
                    raw_source={
                        "path": str(path),
                        "uploaded_at": path.stat().st_mtime,
                    },
                    relevance_score=1.0,
                    recency_score=0.6,
                    completeness_score=0.6,
                    rank_score=0.9,
                    created_at=now_iso(),
                    updated_at=now_iso(),
                )
            )
        return papers

    @staticmethod
    def _query_window_for_adapter(adapter_name: str) -> int:
        if adapter_name == "arxiv":
            return 1
        if adapter_name in {"crossref", "pubmed", "dblp", "openreview", "acl-anthology", "semantic-scholar"}:
            return 3
        return 5

    def _core_papers_for_synthesis(self, project: ResearchProject, papers: list[PaperRecord]) -> list[PaperRecord]:
        metadata = project.metadata or {}
        limit = metadata.get("core_paper_limit") or 24
        bounded_limit = max(20, min(int(limit), 40))
        return select_core_papers(papers, limit=bounded_limit)

    def _collection_audit(self, papers: list[PaperRecord], references: list[ReferenceEntry]) -> dict[str, Any]:
        included_papers = [paper for paper in papers if self._include_reference_in_export(paper)]
        excluded_reasons: list[dict[str, Any]] = []
        for paper in papers:
            if self._include_reference_in_export(paper):
                continue
            reasons: list[str] = []
            if not paper.title:
                reasons.append("missing-title")
            if not (paper.doi or paper.source_url or paper.oa_url):
                reasons.append("missing-resolvable-source")
            if not paper.provider:
                reasons.append("missing-provider")
            excluded_reasons.append(
                {
                    "paper_id": paper.paper_id,
                    "title": paper.title,
                    "provider": paper.provider,
                    "reasons": reasons or ["failed-reference-eligibility"],
                }
            )

        canonical_versions = [
            {
                "paper_id": paper.paper_id,
                "canonical_id": paper.canonical_id,
                "canonical_source": paper.canonical_source,
                "reason": canonical_reason(paper),
            }
            for paper in included_papers
        ]
        return {
            "provider_breakdown": provider_breakdown(papers),
            "venue_breakdown": venue_breakdown(papers),
            "preprint_ratio": preprint_ratio(included_papers),
            "canonical_reference_count": len([entry for entry in references if entry.included_in_final]),
            "canonical_versions": canonical_versions,
            "excluded_from_final_references": excluded_reasons,
        }

    @staticmethod
    def _extract_local_title(path: Path, content: str) -> str:
        for line in content.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if len(stripped) >= 6:
                return stripped
        return path.stem.replace("_", " ").replace("-", " ").strip() or "Uploaded paper"

    @staticmethod
    def _extract_doi(content: str) -> str | None:
        match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", content, flags=re.IGNORECASE)
        return match.group(0) if match else None

    @staticmethod
    def _extract_year(content: str) -> int | None:
        match = re.search(r"\b(19|20)\d{2}\b", content[:5000])
        if not match:
            return None
        return int(match.group(0))

    def _build_outline(self, project: ResearchProject, papers: list[PaperRecord]) -> list[OutlineNodeRecord]:
        now = now_iso()
        sections = [
            (
                "landscape",
                "Research Landscape and Problem Framing",
                "Define the research landscape, core problem, and why the topic matters now.",
            ),
            (
                "methods",
                "Methods and Technical Routes",
                "Compare the dominant methods, study designs, and technical routes in the literature.",
            ),
            (
                "evidence",
                "Empirical Evidence and Application Scenarios",
                "Synthesize the most concrete findings, applications, and scenario-specific results.",
            ),
            (
                "limitations",
                "Limitations and Conflicting Findings",
                "Surface limitations, contradictions, and unresolved debates across the evidence pool.",
            ),
            (
                "innovation",
                "Candidate Innovation Directions",
                "Condense evidence-backed research gaps into candidate innovation directions.",
            ),
        ]
        return [
            OutlineNodeRecord(
                node_id=f"outline:{project.project_id}:{key}",
                project_id=project.project_id,
                title=title,
                purpose=purpose,
                section_order=index + 1,
                claim_spans=[],
                metadata={"section_key": key},
                created_at=now,
                updated_at=now,
            )
            for index, (key, title, purpose) in enumerate(sections)
        ]

    def _build_evidence_cards(
        self,
        project: ResearchProject,
        papers: list[PaperRecord],
        outline: list[OutlineNodeRecord],
    ) -> list[EvidenceCardRecord]:
        outline_by_key = {item.metadata.get("section_key"): item for item in outline}
        cards: list[EvidenceCardRecord] = []
        for paper in papers:
            section_keys = self._section_keys_for_paper(paper)
            outline_ids = [outline_by_key[key].node_id for key in section_keys if key in outline_by_key]
            cards.append(
                EvidenceCardRecord(
                    evidence_id=str(uuid.uuid4()),
                    project_id=project.project_id,
                    paper_id=paper.paper_id,
                    summary=summarize_abstract(paper.abstract or paper.title),
                    claim_spans=[
                        f"Title: {paper.title}",
                        f"Venue/Year: {(paper.venue or 'Unknown venue')} ({paper.year or 'n.d.'})",
                    ],
                    outline_node_ids=outline_ids,
                    relevance_score=paper.relevance_score,
                    recency_score=paper.recency_score,
                    evidence_level="summary+metadata" if paper.abstract else "metadata-only",
                    method_tags=paper.methods,
                    novelty_tags=self._novelty_tags_for_paper(paper),
                    source_snapshot={
                        "provider": paper.provider,
                        "source_url": paper.source_url,
                        "doi": paper.doi,
                    },
                    created_at=now_iso(),
                    updated_at=now_iso(),
                )
            )

        self._ensure_minimum_section_coverage(cards, outline, papers)
        return cards

    def _ensure_minimum_section_coverage(
        self,
        cards: list[EvidenceCardRecord],
        outline: list[OutlineNodeRecord],
        papers: list[PaperRecord],
    ) -> None:
        outline_ids = [node.node_id for node in outline]
        card_by_paper = {card.paper_id: card for card in cards}
        ranked_papers = sorted(papers, key=lambda item: item.rank_score, reverse=True)
        for outline_id in outline_ids:
            attached = [card for card in cards if outline_id in card.outline_node_ids]
            if len(attached) >= 2:
                continue
            for paper in ranked_papers:
                card = card_by_paper[paper.paper_id]
                if outline_id in card.outline_node_ids:
                    continue
                card.outline_node_ids.append(outline_id)
                attached.append(card)
                if len(attached) >= 2:
                    break

    def _build_graph_edges(
        self,
        project: ResearchProject,
        papers: list[PaperRecord],
        evidence_cards: list[EvidenceCardRecord],
        outline: list[OutlineNodeRecord],
    ) -> list[PaperEdgeRecord]:
        outline_lookup = {node.node_id: node for node in outline}
        edges: list[PaperEdgeRecord] = []
        now = now_iso()

        by_canonical = {paper.canonical_id: paper for paper in papers}
        for paper in papers:
            referenced = paper.raw_source.get("referenced_works", [])
            if isinstance(referenced, list):
                for ref in referenced[:12]:
                    target_paper = next(
                        (candidate for candidate in by_canonical.values() if candidate.provider_id == ref or candidate.source_url == ref),
                        None,
                    )
                    edges.append(
                        PaperEdgeRecord(
                            edge_id=str(uuid.uuid4()),
                            project_id=project.project_id,
                            source_paper_id=paper.paper_id,
                            relation_type="cites",
                            target_kind="paper",
                            target_ref=ref,
                            target_paper_id=target_paper.paper_id if target_paper else None,
                            created_at=now,
                        )
                    )

        for card in evidence_cards:
            for outline_node_id in card.outline_node_ids:
                outline_node = outline_lookup.get(outline_node_id)
                edges.append(
                    PaperEdgeRecord(
                        edge_id=str(uuid.uuid4()),
                        project_id=project.project_id,
                        source_paper_id=card.paper_id,
                        relation_type="supports",
                        target_kind="claim",
                        target_ref=outline_node.title if outline_node else outline_node_id,
                        target_outline_node_id=outline_node_id,
                        metadata={"evidence_id": card.evidence_id},
                        created_at=now,
                    )
                )
        return edges

    def _build_references(self, papers: list[PaperRecord]) -> list[ReferenceEntry]:
        references = [format_apa7_reference(paper) for paper in papers]
        seen: set[str] = set()
        deduped: list[ReferenceEntry] = []
        for entry in references:
            key = normalize_title_key(entry.formatted_text)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)
        return deduped

    async def _write_exports(
        self,
        *,
        project: ResearchProject,
        output_dir: Path,
        all_papers: list[PaperRecord],
        core_papers: list[PaperRecord],
        outline: list[OutlineNodeRecord],
        evidence_cards: list[EvidenceCardRecord],
        references: list[ReferenceEntry],
        graph: AcademicGraph | None,
    ) -> list[Path]:
        export_dir = output_dir / "academic-research" / f"{slugify(project.topic)}-{project.project_id[:8]}"
        export_dir.mkdir(parents=True, exist_ok=True)

        report_path = export_dir / "report.md"
        references_path = export_dir / "references.md"
        bibtex_path = export_dir / "references.bib"
        evidence_map_path = export_dir / "evidence_map.json"
        audit_path = export_dir / "retrieval_audit.json"
        graph_path = export_dir / "graph.json"

        evidence_map = self._build_evidence_map(project, outline, evidence_cards, core_papers)
        retrieval_audit = self._collection_audit(all_papers, references)
        report_path.write_text(
            self._render_report(project, outline, evidence_cards, core_papers, references),
            encoding="utf-8",
        )
        references_path.write_text(
            self._render_references(project, references),
            encoding="utf-8",
        )
        bibtex_path.write_text(
            "\n\n".join(format_bibtex_entry(paper) for paper in all_papers if self._include_reference_in_export(paper)),
            encoding="utf-8",
        )
        evidence_map_path.write_text(
            json.dumps(evidence_map, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        audit_path.write_text(
            json.dumps(retrieval_audit, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if graph is not None:
            graph_path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")

        exports = [report_path, references_path, bibtex_path, evidence_map_path, audit_path]
        if graph is not None:
            exports.append(graph_path)
        return exports

    def _render_report(
        self,
        project: ResearchProject,
        outline: list[OutlineNodeRecord],
        evidence_cards: list[EvidenceCardRecord],
        papers: list[PaperRecord],
        references: list[ReferenceEntry],
    ) -> str:
        paper_lookup = {paper.paper_id: paper for paper in papers}
        cards_by_outline: dict[str, list[EvidenceCardRecord]] = {}
        for card in evidence_cards:
            for outline_node_id in card.outline_node_ids:
                cards_by_outline.setdefault(outline_node_id, []).append(card)

        lines = [
            f"# {project.topic}",
            "",
            f"- Project ID: `{project.project_id}`",
            f"- Topic Scope: {project.scope or 'Not specified'}",
            f"- Domain: {project.domain}",
            f"- Generated: {today_stamp()}",
            f"- Core Evidence Set: {len(papers)} papers used for synthesis",
            "",
            "## Executive Summary",
            "",
            (
                f"This report synthesizes {len(papers)} core papers for the topic **{project.topic}**. "
                "The literature was normalized across multiple scholarly metadata providers and ranked by "
                "topic relevance, metadata completeness, recency, and citation strength."
            ),
            "",
        ]

        for node in outline:
            lines.append(f"## {node.title}")
            lines.append("")
            lines.append(node.purpose)
            lines.append("")
            node_cards = sorted(
                cards_by_outline.get(node.node_id, []),
                key=lambda item: (item.relevance_score, item.recency_score),
                reverse=True,
            )[:4]
            for card in node_cards:
                paper = paper_lookup.get(card.paper_id)
                if paper is None:
                    continue
                lines.append(
                    f"- {paper.title} {_author_year_citation(paper)}: {card.summary}"
                )
            if node.metadata.get("section_key") == "innovation":
                lines.append("")
                lines.append("### Candidate Innovation Directions")
                lines.extend(
                    self._render_innovation_directions(papers)
                )
            lines.append("")

        lines.append("## References")
        lines.append("")
        for entry in references:
            if entry.included_in_final:
                lines.append(f"- {entry.formatted_text}")
        lines.append("")
        lines.append(
            "Full export bundle: `report.md`, `references.md`, `references.bib`, `evidence_map.json`, and `retrieval_audit.json`."
        )
        return "\n".join(lines).strip() + "\n"

    def _render_references(self, project: ResearchProject, references: list[ReferenceEntry]) -> str:
        lines = [f"# References for {project.topic}", "", "Style: APA 7", ""]
        for entry in references:
            if entry.included_in_final:
                lines.append(f"- {entry.formatted_text}")
        return "\n".join(lines).strip() + "\n"

    def _build_evidence_map(
        self,
        project: ResearchProject,
        outline: list[OutlineNodeRecord],
        evidence_cards: list[EvidenceCardRecord],
        papers: list[PaperRecord],
    ) -> dict[str, Any]:
        paper_lookup = {paper.paper_id: paper for paper in papers}
        return {
            "project_id": project.project_id,
            "topic": project.topic,
            "outline": [
                {
                    "node_id": node.node_id,
                    "title": node.title,
                    "purpose": node.purpose,
                    "evidence": [
                        {
                            "evidence_id": card.evidence_id,
                            "paper_id": card.paper_id,
                            "paper_title": paper_lookup.get(card.paper_id).title if paper_lookup.get(card.paper_id) else None,
                            "summary": card.summary,
                            "novelty_tags": card.novelty_tags,
                        }
                        for card in evidence_cards
                        if node.node_id in card.outline_node_ids
                    ],
                }
                for node in outline
            ],
        }

    def _render_innovation_directions(self, papers: list[PaperRecord]) -> list[str]:
        bullets = []
        population_gap = next((paper for paper in papers if paper.populations), None)
        method_gap = next((paper for paper in papers if len(paper.methods) >= 2), None)
        conflict_gap = next((paper for paper in papers if paper.conflict_flags), None)
        design_gap = next(
            (paper for paper in papers if "benchmark" in " ".join(paper.methods + paper.keywords).lower() or "dataset" in (paper.abstract or "").lower()),
            None,
        )

        if population_gap:
            bullets.append(
                f"- Research-object gap: extend the topic toward under-described populations or scenarios highlighted by **{population_gap.title}** {_author_year_citation(population_gap)}."
            )
        if method_gap:
            bullets.append(
                f"- Method-combination gap: combine complementary methods observed in **{method_gap.title}** {_author_year_citation(method_gap)} to test whether mixed pipelines outperform single-route studies."
            )
        if conflict_gap:
            bullets.append(
                f"- Conflicting-findings gap: resolve contradictory evidence surfaced in **{conflict_gap.title}** {_author_year_citation(conflict_gap)} with better-controlled replication or stratified analysis."
            )
        if design_gap:
            bullets.append(
                f"- Dataset/design limitation: strengthen benchmarking, sampling, or external validation beyond the setup described in **{design_gap.title}** {_author_year_citation(design_gap)}."
            )
        if not bullets:
            bullets.append("- Research-object gap: extend the current evidence base toward less-studied populations, contexts, or datasets.")
            bullets.append("- Method-combination gap: compare hybrid approaches instead of single isolated methods.")
            bullets.append("- Conflicting-findings gap: design targeted replication studies to reconcile inconsistent conclusions.")
            bullets.append("- Dataset/design limitation: improve dataset diversity, benchmark coverage, or experimental controls.")
        return bullets

    @staticmethod
    def _section_keys_for_paper(paper: PaperRecord) -> list[str]:
        text = f"{paper.title} {paper.abstract or ''}".lower()
        keys = ["landscape"]
        if paper.methods or any(token in text for token in ("method", "framework", "model", "trial", "dataset")):
            keys.append("methods")
        if any(token in text for token in ("application", "result", "case", "empirical", "patient", "deployment", "evaluation")):
            keys.append("evidence")
        if paper.conflict_flags or any(token in text for token in ("limitation", "challenge", "risk", "bias", "controvers")):
            keys.append("limitations")
        if any(token in text for token in ("future", "gap", "opportun", "open question")) or paper.methods or paper.populations:
            keys.append("innovation")
        return merge_unique(keys)

    @staticmethod
    def _novelty_tags_for_paper(paper: PaperRecord) -> list[str]:
        tags: list[str] = []
        if paper.populations:
            tags.append("research-object-gap")
        if len(paper.methods) >= 2:
            tags.append("method-combination-gap")
        if paper.conflict_flags:
            tags.append("conflicting-findings")
        if "dataset" in (paper.abstract or "").lower() or "benchmark" in (paper.abstract or "").lower():
            tags.append("dataset-or-design-limitation")
        return merge_unique(tags)

    @staticmethod
    def _include_reference_in_export(paper: PaperRecord) -> bool:
        return bool(
            paper.title
            and paper.provider
            and paper.canonical_source
            and (paper.doi or paper.source_url or paper.oa_url)
        )

    @staticmethod
    def _to_virtual_output(thread_id: str, path: Path) -> str:
        outputs_root = get_paths().sandbox_outputs_dir(thread_id).resolve()
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(outputs_root)
        except ValueError:
            return str(resolved)
        return f"{VIRTUAL_PATH_PREFIX}/outputs/{relative.as_posix()}"

    async def _require_project(self, project_id: str) -> ResearchProject:
        project = await self._repository.get_project(project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")
        return project


def _author_year_citation(paper: PaperRecord) -> str:
    if paper.authors:
        lead = paper.authors[0].family_name or paper.authors[0].display_name.split(" ")[-1]
        if len(paper.authors) == 1:
            label = lead
        else:
            label = f"{lead} et al."
    else:
        label = paper.title[:32].rstrip()
    year = paper.year if paper.year is not None else "n.d."
    return f"({label}, {year})"
