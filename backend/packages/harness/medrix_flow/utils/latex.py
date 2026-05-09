"""Utilities for preparing and compiling LaTeX artifacts."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve

_REMOTE_GRAPHICS_RE = re.compile(r"(\\includegraphics(?:\[[^\]]*\])?\{)(https?://[^}]+)(\})")
_SUBSCRIPT_CHARS = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
    "₌": "=",
    "₍": "(",
    "₎": ")",
    "ₐ": "a",
    "ₑ": "e",
    "ₕ": "h",
    "ᵢ": "i",
    "ⱼ": "j",
    "ₖ": "k",
    "ₗ": "l",
    "ₘ": "m",
    "ₙ": "n",
    "ₒ": "o",
    "ₚ": "p",
    "ᵣ": "r",
    "ₛ": "s",
    "ₜ": "t",
    "ᵤ": "u",
    "ᵥ": "v",
    "ₓ": "x",
}
_SUPERSCRIPT_CHARS = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁼": "=",
    "⁽": "(",
    "⁾": ")",
    "ᵃ": "a",
    "ᵇ": "b",
    "ᶜ": "c",
    "ᵈ": "d",
    "ᵉ": "e",
    "ᶠ": "f",
    "ᵍ": "g",
    "ʰ": "h",
    "ⁱ": "i",
    "ʲ": "j",
    "ᵏ": "k",
    "ˡ": "l",
    "ᵐ": "m",
    "ⁿ": "n",
    "ᵒ": "o",
    "ᵖ": "p",
    "ʳ": "r",
    "ˢ": "s",
    "ᵗ": "t",
    "ᵘ": "u",
    "ᵛ": "v",
    "ʷ": "w",
    "ˣ": "x",
    "ʸ": "y",
    "ᶻ": "z",
}
_SUBSCRIPT_CLASS = "".join(map(re.escape, _SUBSCRIPT_CHARS))
_SUPERSCRIPT_CLASS = "".join(map(re.escape, _SUPERSCRIPT_CHARS))
_UNICODE_MATH_TOKEN_RE = re.compile(
    rf"(?<![$\\])([A-Za-z0-9]+)([{_SUBSCRIPT_CLASS}{_SUPERSCRIPT_CLASS}]+)"
)
_ADJACENT_INLINE_MATH_RATIO_RE = re.compile(r"\$([^$]+)\$/\$([^$]+)\$")


def _translate_script_chars(chars: str, mapping: dict[str, str]) -> str:
    return "".join(mapping[ch] for ch in chars if ch in mapping)


def _replace_unicode_math_tokens(source: str) -> str:
    def repl(match: re.Match[str]) -> str:
        base = match.group(1)
        scripts = match.group(2)
        pieces: list[str] = [base]
        idx = 0
        while idx < len(scripts):
            char = scripts[idx]
            if char in _SUBSCRIPT_CHARS:
                start = idx
                while idx < len(scripts) and scripts[idx] in _SUBSCRIPT_CHARS:
                    idx += 1
                translated = _translate_script_chars(scripts[start:idx], _SUBSCRIPT_CHARS)
                pieces.append(f"_{{{translated}}}")
                continue
            if char in _SUPERSCRIPT_CHARS:
                start = idx
                while idx < len(scripts) and scripts[idx] in _SUPERSCRIPT_CHARS:
                    idx += 1
                translated = _translate_script_chars(scripts[start:idx], _SUPERSCRIPT_CHARS)
                pieces.append(f"^{{{translated}}}")
                continue
            idx += 1
        return f"${''.join(pieces)}$"

    source = _UNICODE_MATH_TOKEN_RE.sub(repl, source)
    previous = None
    while previous != source:
        previous = source
        source = _ADJACENT_INLINE_MATH_RATIO_RE.sub(r"$\1/\2$", source)
    return source


def _sanitize_latex_source(source: str) -> str:
    source = _replace_unicode_math_tokens(source)
    if "\\usepackage{subfig}" not in source and "\\subfloat" in source:
        source = source.replace("\\usepackage{graphicx}", "\\usepackage{graphicx}\n\\usepackage{subfig}", 1)
    if "\\usepackage{amsmath}" not in source and ("$" in source or "\\[" in source or "\\begin{equation" in source):
        source = source.replace("\\usepackage{graphicx}", "\\usepackage{graphicx}\n\\usepackage{amsmath}", 1)
    if "\\hypersetup{" not in source and "\\usepackage{hyperref}" in source:
        source = source.replace("\\usepackage{hyperref}", "\\usepackage{hyperref}\n\\hypersetup{hidelinks}", 1)
    return source


def _download_remote_graphics(source: str, workdir: Path) -> str:
    workdir.mkdir(parents=True, exist_ok=True)

    def repl(match: re.Match[str]) -> str:
        prefix, url, suffix = match.groups()
        parsed = urlparse(url)
        filename = Path(parsed.path).name or "figure"
        local_path = workdir / filename
        if not local_path.suffix:
            local_path = local_path.with_suffix(".png")
        try:
            urlretrieve(url, local_path)
            return f"{prefix}{local_path.name}{suffix}"
        except Exception:
            return match.group(0)

    return _REMOTE_GRAPHICS_RE.sub(repl, source)


def prepare_latex_preview(tex_path: Path, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or tex_path.parent / ".latex-preview"
    output_dir.mkdir(parents=True, exist_ok=True)
    source = tex_path.read_text(encoding="utf-8")
    source = _sanitize_latex_source(source)
    source = _download_remote_graphics(source, output_dir)
    prepared_path = output_dir / tex_path.name
    prepared_path.write_text(source, encoding="utf-8")
    return prepared_path


def compile_latex_to_pdf(tex_path: Path, output_dir: Path | None = None) -> Path:
    tectonic = shutil.which("tectonic")
    if tectonic is None:
        raise FileNotFoundError("tectonic not found in PATH")

    output_dir = output_dir or tex_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        [tectonic, "-k", "--outdir", str(output_dir), str(tex_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "tectonic compilation failed").strip())

    pdf_path = output_dir / tex_path.with_suffix(".pdf").name
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not produced: {pdf_path}")
    return pdf_path
