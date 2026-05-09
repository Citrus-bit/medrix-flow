"""One-shot LaTeX manuscript export tool."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Annotated, Any

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from medrix_flow.agents.thread_state import ThreadState
from medrix_flow.config.paths import VIRTUAL_PATH_PREFIX
from medrix_flow.utils.citations import CitationAuditResult, audit_latex_citations, write_citation_audit
from medrix_flow.utils.latex import compile_latex_to_pdf, prepare_latex_preview

OUTPUTS_VIRTUAL_PREFIX = f"{VIRTUAL_PATH_PREFIX}/outputs"
_SAFE_FILENAME_STEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _safe_filename_stem(filename_stem: str | None) -> str:
    stem = (filename_stem or "manuscript").strip()
    if stem.lower().endswith((".tex", ".pdf")):
        stem = stem.rsplit(".", 1)[0]

    if not stem or stem in {".", ".."} or "/" in stem or "\\" in stem:
        raise ValueError("filename_stem must be a filename stem, not a path")
    if not _SAFE_FILENAME_STEM_RE.fullmatch(stem):
        raise ValueError("filename_stem may only contain ASCII letters, numbers, dots, underscores, and hyphens")
    return stem


def _outputs_dir(runtime: ToolRuntime[ContextT, ThreadState]) -> Path:
    if runtime.state is None:
        raise ValueError("Thread runtime state is not available")
    if not runtime.context.get("thread_id"):
        raise ValueError("Thread ID is not available in runtime context")

    thread_data = runtime.state.get("thread_data") or {}
    outputs_path = thread_data.get("outputs_path")
    if not outputs_path:
        raise ValueError("Thread outputs path is not available in runtime state")

    outputs_dir = Path(outputs_path).resolve()
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir


def _virtual_output_path(outputs_dir: Path, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(outputs_dir)
    except ValueError as exc:
        raise ValueError(f"Tool attempted to write outside {OUTPUTS_VIRTUAL_PREFIX}: {path}") from exc
    return f"{OUTPUTS_VIRTUAL_PREFIX}/{relative.as_posix()}"


def _parse_claim_map(claim_map_json: str | None) -> Any | None:
    if claim_map_json is None or not claim_map_json.strip():
        return None
    try:
        return json.loads(claim_map_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"claim_map_json is not valid JSON: {exc}") from exc


def _write_claim_map(claim_map: Any | None, claim_map_path: Path) -> Path | None:
    if claim_map is None:
        return None
    claim_map_path.write_text(json.dumps(claim_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return claim_map_path


def _write_manuscript_inputs(
    *,
    tex_path: Path,
    bibtex_path: Path,
    claim_map_path: Path,
    tex_content: str,
    bibtex_content: str,
    claim_map: Any | None,
) -> Path | None:
    tex_path.write_text(tex_content, encoding="utf-8")
    bibtex_path.write_text(bibtex_content, encoding="utf-8")
    return _write_claim_map(claim_map, claim_map_path)


def _artifact_paths(outputs_dir: Path, *paths: Path) -> list[str]:
    return [_virtual_output_path(outputs_dir, path) for path in paths]


def _format_audit_failure(result: CitationAuditResult) -> str:
    parts = ["FAIL: citation audit blocked PDF generation."]
    if result.violations:
        parts.append("Violations: " + " ".join(result.violations))
    if result.missing_keys:
        parts.append("Missing keys: " + ", ".join(result.missing_keys) + ".")
    if result.unsupported_claims:
        parts.append(f"Unsupported claims: {len(result.unsupported_claims)}.")
    return " ".join(parts)


def _compile_pdf(tex_path: Path, bibtex_path: Path) -> Path:
    prepared_path = prepare_latex_preview(tex_path)
    prepared_bibtex_path = prepared_path.parent / bibtex_path.name
    if prepared_bibtex_path.resolve() != bibtex_path.resolve():
        shutil.copy2(bibtex_path, prepared_bibtex_path)

    preview_pdf = compile_latex_to_pdf(prepared_path, prepared_path.parent)
    final_pdf = tex_path.with_suffix(".pdf")
    if preview_pdf.resolve() != final_pdf.resolve():
        shutil.copy2(preview_pdf, final_pdf)
    return final_pdf


@tool("manuscript_export", parse_docstring=True)
def manuscript_export_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    tex_content: str,
    bibtex_content: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    claim_map_json: str | None = None,
    filename_stem: str = "manuscript",
    allow_nocite_all: bool = False,
) -> Command:
    """Write a LaTeX manuscript bundle, audit citations, compile PDF, and present artifacts.

    Use this tool for final paper, review article, experiment-paper, or formal
    manuscript deliverables. It writes the manuscript files under
    `/mnt/user-data/outputs`, validates BibTeX citation keys, blocks unsafe
    `\\nocite{*}` fallbacks by default, compiles the PDF when the audit passes,
    and returns the generated artifacts to the user.

    Args:
        tex_content: Full LaTeX source for the manuscript.
        bibtex_content: Full BibTeX source for `references.bib`.
        claim_map_json: Optional JSON claim/evidence map used to block unsupported claims.
        filename_stem: Safe output filename stem for `{filename_stem}.tex` and `{filename_stem}.pdf`.
        allow_nocite_all: Set true only when the user explicitly requested `\\nocite{*}`.
    """
    try:
        stem = _safe_filename_stem(filename_stem)
        claim_map = _parse_claim_map(claim_map_json)
        outputs_dir = _outputs_dir(runtime)

        tex_path = outputs_dir / f"{stem}.tex"
        bibtex_path = outputs_dir / "references.bib"
        audit_path = outputs_dir / "citation_audit.json"
        claim_map_path = outputs_dir / "claim_map.json"
        final_pdf_path = tex_path.with_suffix(".pdf")
        if final_pdf_path.exists():
            final_pdf_path.unlink()

        resolved_claim_map_path = _write_manuscript_inputs(
            tex_path=tex_path,
            bibtex_path=bibtex_path,
            claim_map_path=claim_map_path,
            tex_content=tex_content,
            bibtex_content=bibtex_content,
            claim_map=claim_map,
        )

        audit_result = audit_latex_citations(
            bibtex_path=bibtex_path,
            tex_path=tex_path,
            claim_map_path=resolved_claim_map_path,
            allow_nocite_all=allow_nocite_all,
        )
        write_citation_audit(audit_result, audit_path)

        if not audit_result.passed:
            artifacts = _artifact_paths(outputs_dir, audit_path, tex_path, bibtex_path)
            return Command(
                update={
                    "artifacts": artifacts,
                    "messages": [ToolMessage(_format_audit_failure(audit_result), tool_call_id=tool_call_id)],
                }
            )

        try:
            final_pdf_path = _compile_pdf(tex_path, bibtex_path)
        except Exception as exc:
            if final_pdf_path.exists():
                final_pdf_path.unlink()
            artifacts = _artifact_paths(outputs_dir, tex_path, bibtex_path, audit_path)
            message = f"FAIL: LaTeX compilation failed after citation audit passed: {exc}"
            return Command(
                update={
                    "artifacts": artifacts,
                    "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
                }
            )

        artifacts = _artifact_paths(outputs_dir, final_pdf_path, tex_path, bibtex_path, audit_path)
        message = (
            f"PASS: manuscript_export wrote `{_virtual_output_path(outputs_dir, final_pdf_path)}`. "
            f"BibTeX keys: {len(audit_result.citation_keys)}; cited keys: {len(audit_result.cited_keys)}."
        )
        return Command(
            update={
                "artifacts": artifacts,
                "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
            }
        )
    except Exception as exc:
        return Command(update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]})
