import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

from starlette.requests import Request

import app.gateway.routers.artifacts as artifacts_router


def test_get_artifact_reads_utf8_text_file_on_windows_locale(tmp_path, monkeypatch) -> None:
    artifact_path = tmp_path / "note.txt"
    text = "Curly quotes: \u201cutf8\u201d"
    artifact_path.write_text(text, encoding="utf-8")

    original_read_text = Path.read_text

    def read_text_with_gbk_default(self, *args, **kwargs):
        kwargs.setdefault("encoding", "gbk")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text_with_gbk_default)
    monkeypatch.setattr(artifacts_router, "resolve_thread_virtual_path", lambda _thread_id, _path: artifact_path)

    request = Request({"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""})
    response = asyncio.run(artifacts_router.get_artifact("thread-1", "mnt/user-data/outputs/note.txt", request))

    assert bytes(response.body).decode("utf-8") == text
    assert response.media_type == "text/plain"


def test_list_thread_artifacts_reads_outputs_directory_and_sorts_by_mtime(tmp_path, monkeypatch) -> None:
    outputs_dir = tmp_path / "outputs"
    figures_dir = outputs_dir / "figures"
    hidden_dir = outputs_dir / ".latex-preview"
    figures_dir.mkdir(parents=True)
    hidden_dir.mkdir(parents=True)

    older = outputs_dir / "report.md"
    newer = figures_dir / "roc.png"
    hidden = hidden_dir / "preview.log"
    older.write_text("# report", encoding="utf-8")
    newer.write_bytes(b"png")
    hidden.write_text("tmp", encoding="utf-8")

    os.utime(older, (1_700_000_000, 1_700_000_000))
    os.utime(newer, (1_700_000_100, 1_700_000_100))

    monkeypatch.setattr(
        artifacts_router,
        "get_paths",
        lambda: SimpleNamespace(sandbox_outputs_dir=lambda _thread_id: outputs_dir),
    )

    response = asyncio.run(artifacts_router.list_thread_artifacts("thread-1"))

    assert [item.filepath for item in response.files] == [
        "/mnt/user-data/outputs/figures/roc.png",
        "/mnt/user-data/outputs/report.md",
    ]
    assert all(".latex-preview" not in item.filepath for item in response.files)
