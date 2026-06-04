"""Shared fixtures for pytest."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """A temporary directory with sample files."""
    (tmp_path / "photo_001.jpg").write_bytes(b"fake jpg")
    (tmp_path / "photo_002.png").write_bytes(b"fake png")
    (tmp_path / "report_2026.pdf").write_bytes(b"fake pdf")
    (tmp_path / "budget.xlsx").write_bytes(b"fake xlsx")
    (tmp_path / "notes.txt").write_text("hello")
    (tmp_path / "archive.zip").write_bytes(b"fake zip")
    (tmp_path / "song.mp3").write_bytes(b"fake mp3")
    (tmp_path / "video.mp4").write_bytes(b"fake mp4")
    return tmp_path
