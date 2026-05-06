"""Tests for LaTeX artifact handling in present_files."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

present_file_tool_module = importlib.import_module("medrix_flow.tools.builtins.present_file_tool")
latex_utils = importlib.import_module("medrix_flow.utils.latex")


def _make_runtime(outputs_path: str) -> SimpleNamespace:
    return SimpleNamespace(
        state={"thread_data": {"outputs_path": outputs_path}},
        context={"thread_id": "thread-1"},
    )


def test_present_files_adds_pdf_for_tex(tmp_path, monkeypatch):
    outputs_dir = tmp_path / "threads" / "thread-1" / "user-data" / "outputs"
    outputs_dir.mkdir(parents=True)
    tex_path = outputs_dir / "report.tex"
    tex_path.write_text("\\documentclass{article}\\begin{document}hi\\end{document}", encoding="utf-8")

    preview_dir = tmp_path / "preview"
    preview_dir.mkdir()
    preview_tex = preview_dir / "report.tex"
    preview_pdf = preview_dir / "report.pdf"
    preview_tex.write_text("prepared", encoding="utf-8")
    preview_pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        present_file_tool_module,
        "prepare_latex_preview",
        lambda _tex_path: preview_tex,
    )
    monkeypatch.setattr(
        present_file_tool_module,
        "compile_latex_to_pdf",
        lambda _tex_path, _output_dir=None: preview_pdf,
    )

    result = present_file_tool_module.present_file_tool.func(
        runtime=_make_runtime(str(outputs_dir)),
        filepaths=[str(tex_path)],
        tool_call_id="tc-1",
    )

    assert result.update["artifacts"] == [
        "/mnt/user-data/outputs/report.pdf",
        "/mnt/user-data/outputs/report.tex",
    ]


def test_prepare_latex_preview_converts_unicode_subscripts(tmp_path):
    tex_path = tmp_path / "report.tex"
    tex_path.write_text(
        "\\documentclass{article}\n"
        "\\usepackage{graphicx}\n"
        "\\begin{document}\n"
        "Turns ratio N₁/N₂ and current I₀.\n"
        "\\end{document}\n",
        encoding="utf-8",
    )

    prepared = latex_utils.prepare_latex_preview(tex_path)
    content = prepared.read_text(encoding="utf-8")

    assert "\\usepackage{amsmath}" in content
    assert "$N_{1}/N_{2}$" in content
    assert "$I_{0}$" in content
