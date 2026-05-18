"""Tests for deterministic BibTeX key extraction and LaTeX citation auditing."""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

from medrix_flow.utils.citations import audit_latex_citations, extract_bibtex_keys, extract_latex_citations

citation_audit_tool_module = importlib.import_module("medrix_flow.tools.builtins.citation_audit_tool")


def _make_runtime(outputs_path: str, uploads_path: str | None = None, workspace_path: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        state={
            "thread_data": {
                "outputs_path": outputs_path,
                "uploads_path": uploads_path,
                "workspace_path": workspace_path,
            }
        },
        context={"thread_id": "thread-1"},
    )


def test_extract_bibtex_keys_ignores_non_reference_entries():
    source = """
@string{jmlr = {Journal of Machine Learning Research}}
@article{smith2024,
  title = {A paper}
}
@comment{ignored, note = {not a reference}}
@inproceedings{doe-2025:demo,
  title = {Another paper}
}
"""

    assert extract_bibtex_keys(source) == ["smith2024", "doe-2025:demo"]


def test_latex_citation_audit_flags_missing_keys_and_nocite_all(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    tex_path = tmp_path / "manuscript.tex"
    bibtex_path.write_text("@article{smith2024,\n  title = {A paper}\n}\n", encoding="utf-8")
    tex_path.write_text(
        r"""
\documentclass{article}
\begin{document}
Supported \cite{smith2024}; missing \citep{unknown2025}.
\nocite{*}
\end{document}
""",
        encoding="utf-8",
    )

    result = audit_latex_citations(bibtex_path=bibtex_path, tex_path=tex_path)

    assert result.status == "fail"
    assert result.citation_keys == ["smith2024"]
    assert result.cited_keys == ["smith2024", "unknown2025"]
    assert result.missing_keys == ["unknown2025"]
    assert result.nocite_all is True
    assert len(result.violations) == 2


def test_latex_citation_extraction_ignores_comments():
    cited, nocite_all = extract_latex_citations(
        r"""
Visible \cite{smith2024}
% Hidden \cite{ignored2024}
Escaped percent \% still text \citet{doe2025}
"""
    )

    assert cited == ["smith2024", "doe2025"]
    assert nocite_all is False


def test_latex_citation_audit_blocks_missing_inline_citations_and_author_notes(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    tex_path = tmp_path / "manuscript.tex"
    bibtex_path.write_text("@article{smith2024,\n  title = {A paper}\n}\n", encoding="utf-8")
    tex_path.write_text(
        r"""
\documentclass{article}
\begin{document}
This paragraph is long enough to count as manuscript prose, but it has no inline citation and therefore should be flagged by the audit layer as weak evidence binding.

This paragraph says bibliography keys are synchronized, which is an author process note that must never remain in a final manuscript.
\end{document}
""",
        encoding="utf-8",
    )

    result = audit_latex_citations(bibtex_path=bibtex_path, tex_path=tex_path)

    assert result.status == "fail"
    assert result.paragraph_count == 2
    assert result.uncited_paragraph_count == 2
    assert "bibliography keys are synchronized" in result.author_notes
    assert any("No inline LaTeX citations" in violation for violation in result.violations)
    assert any("Author/tool process notes" in violation for violation in result.violations)


def test_latex_citation_audit_blocks_cited_reference_missing_author(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    tex_path = tmp_path / "manuscript.tex"
    bibtex_path.write_text(
        """
@article{smith2024,
  title = {A paper},
  journal = {Journal},
  year = {2024}
}
""",
        encoding="utf-8",
    )
    tex_path.write_text(r"\documentclass{article}\begin{document}\cite{smith2024}\end{document}", encoding="utf-8")

    result = audit_latex_citations(
        bibtex_path=bibtex_path,
        tex_path=tex_path,
        min_references=1,
        min_cited_references=1,
        min_recent_references=1,
        recent_year_cutoff=2016,
        required_cited_fields=("author", "title", "year"),
    )

    assert result.status == "fail"
    assert result.invalid_references == ["smith2024 missing author"]
    assert any("missing required fields" in violation for violation in result.violations)


def test_latex_citation_audit_accepts_complete_reference_fields(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    tex_path = tmp_path / "manuscript.tex"
    bibtex_path.write_text(
        """
@article{smith2024,
  title = {A paper},
  author = {Smith, Jane},
  journal = {Journal},
  year = {2024},
  url = {https://example.test/smith2024}
}
""",
        encoding="utf-8",
    )
    tex_path.write_text(r"\documentclass{article}\begin{document}\cite{smith2024}\end{document}", encoding="utf-8")

    result = audit_latex_citations(
        bibtex_path=bibtex_path,
        tex_path=tex_path,
        min_references=1,
        min_cited_references=1,
        min_recent_references=1,
        recent_year_cutoff=2016,
        required_cited_fields=("author", "title", "year"),
    )

    assert result.status == "pass"
    assert result.reference_count == 1
    assert result.cited_reference_count == 1
    assert result.recent_reference_count == 1
    assert result.invalid_references == []


def test_latex_citation_audit_blocks_current_unsupported_claim(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    tex_path = tmp_path / "manuscript.tex"
    claim_map_path = tmp_path / "claim_map.json"
    bibtex_path.write_text("@article{smith2024,\n  title = {A paper}\n}\n", encoding="utf-8")
    tex_path.write_text(
        r"\documentclass{article}\begin{document}The method is \textbf{universally} superior. \cite{smith2024}\end{document}",
        encoding="utf-8",
    )
    claim_map_path.write_text(
        json.dumps({"claims": [{"claim": "The method is universally superior.", "support_status": "unsupported"}]}),
        encoding="utf-8",
    )

    result = audit_latex_citations(bibtex_path=bibtex_path, tex_path=tex_path, claim_map_path=claim_map_path)

    assert result.status == "fail"
    assert result.unsupported_claims == ["The method is universally superior."]
    assert result.stale_claims == []
    assert any("Unsupported manuscript claims: 1" in violation for violation in result.violations)


def test_latex_citation_audit_warns_on_stale_unsupported_claim(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    tex_path = tmp_path / "manuscript.tex"
    claim_map_path = tmp_path / "claim_map.json"
    bibtex_path.write_text("@article{smith2024,\n  title = {A paper}\n}\n", encoding="utf-8")
    tex_path.write_text(
        r"\documentclass{article}\begin{document}A weaker supported claim. \cite{smith2024}\end{document}",
        encoding="utf-8",
    )
    claim_map_path.write_text(
        json.dumps({"claims": [{"claim": "The method is universally superior.", "support_status": "unsupported"}]}),
        encoding="utf-8",
    )

    result = audit_latex_citations(bibtex_path=bibtex_path, tex_path=tex_path, claim_map_path=claim_map_path)

    assert result.status == "pass"
    assert result.unsupported_claims == []
    assert result.stale_claims == ["The method is universally superior."]
    assert result.metadata["claim_map_sync_status"] == "stale_entries"


def test_latex_citation_audit_without_tex_keeps_legacy_unsupported_claim_block(tmp_path):
    bibtex_path = tmp_path / "references.bib"
    claim_map_path = tmp_path / "claim_map.json"
    bibtex_path.write_text("@article{smith2024,\n  title = {A paper}\n}\n", encoding="utf-8")
    claim_map_path.write_text(
        json.dumps({"claims": [{"claim": "The method is universally superior.", "support_status": "unsupported"}]}),
        encoding="utf-8",
    )

    result = audit_latex_citations(bibtex_path=bibtex_path, claim_map_path=claim_map_path)

    assert result.status == "fail"
    assert result.unsupported_claims == ["The method is universally superior."]
    assert result.stale_claims == []


def test_citation_audit_tool_writes_audit_artifact(tmp_path, monkeypatch):
    outputs_dir = tmp_path / "threads" / "thread-1" / "user-data" / "outputs"
    outputs_dir.mkdir(parents=True)
    bibtex_path = outputs_dir / "references.bib"
    tex_path = outputs_dir / "manuscript.tex"
    audit_path = outputs_dir / "citation_audit.json"
    bibtex_path.write_text("@article{smith2024,\n  title = {A paper}\n}\n", encoding="utf-8")
    tex_path.write_text(r"\documentclass{article}\begin{document}\cite{smith2024}\end{document}", encoding="utf-8")

    monkeypatch.setattr(
        citation_audit_tool_module,
        "get_paths",
        lambda: SimpleNamespace(resolve_virtual_path=lambda thread_id, path: outputs_dir / path.rsplit("/", 1)[-1]),
    )

    result = citation_audit_tool_module.citation_audit_tool.func(
        runtime=_make_runtime(str(outputs_dir)),
        tool_call_id="tc-1",
        bibtex_path="/mnt/user-data/outputs/references.bib",
        tex_path="/mnt/user-data/outputs/manuscript.tex",
    )

    assert result.update["artifacts"] == ["/mnt/user-data/outputs/citation_audit.json"]
    assert result.update["messages"][0].content.startswith("PASS:")
    assert json.loads(audit_path.read_text(encoding="utf-8"))["status"] == "pass"
