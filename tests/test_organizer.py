"""Tests for the Organizer class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from file_organizer.config import Config
from file_organizer.models import MoveOperation, OrganizePlan
from file_organizer.organizer import Organizer, _human_size, _unique_destination


# ---------------------------------------------------------------------------
# Unit: helpers
# ---------------------------------------------------------------------------


def test_human_size_bytes() -> None:
    assert _human_size(512) == "512.0 B"


def test_human_size_kilobytes() -> None:
    assert _human_size(2048) == "2.0 KB"


def test_human_size_megabytes() -> None:
    assert _human_size(1024 * 1024) == "1.0 MB"


def test_unique_destination_no_conflict(tmp_path: Path) -> None:
    dest = tmp_path / "file.txt"
    assert _unique_destination(dest) == dest


def test_unique_destination_with_conflict(tmp_path: Path) -> None:
    dest = tmp_path / "file.txt"
    dest.write_text("existing")
    result = _unique_destination(dest)
    assert result == tmp_path / "file_1.txt"


def test_unique_destination_multiple_conflicts(tmp_path: Path) -> None:
    for name in ("file.txt", "file_1.txt"):
        (tmp_path / name).write_text("x")
    result = _unique_destination(tmp_path / "file.txt")
    assert result == tmp_path / "file_2.txt"


# ---------------------------------------------------------------------------
# Organizer.scan_files
# ---------------------------------------------------------------------------


def _make_organizer() -> Organizer:
    cfg = Config(
        openai_api_key="sk-test",
        exclude_patterns=["*.pyc", ".DS_Store"],
    )
    return Organizer(cfg)


def test_scan_files_returns_files(tmp_dir: Path) -> None:
    org = _make_organizer()
    files = org.scan_files(tmp_dir)
    names = {f.name for f in files}
    assert "photo_001.jpg" in names
    assert "report_2026.pdf" in names


def test_scan_files_excludes_hidden(tmp_dir: Path) -> None:
    (tmp_dir / ".hidden_file").write_text("secret")
    org = _make_organizer()
    files = org.scan_files(tmp_dir)
    assert not any(f.name.startswith(".") for f in files)


def test_scan_files_excludes_patterns(tmp_dir: Path) -> None:
    (tmp_dir / "cache.pyc").write_bytes(b"")
    org = _make_organizer()
    files = org.scan_files(tmp_dir)
    assert not any(f.extension == "pyc" for f in files)


def test_scan_files_not_recursive_by_default(tmp_dir: Path) -> None:
    subdir = tmp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested")
    org = _make_organizer()
    files = org.scan_files(tmp_dir, recursive=False)
    assert not any(f.name == "nested.txt" for f in files)


def test_scan_files_recursive(tmp_dir: Path) -> None:
    subdir = tmp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested")
    org = _make_organizer()
    files = org.scan_files(tmp_dir, recursive=True)
    assert any(f.name == "nested.txt" for f in files)


# ---------------------------------------------------------------------------
# Organizer.execute
# ---------------------------------------------------------------------------


def test_execute_dry_run_does_not_move(tmp_dir: Path) -> None:
    org = _make_organizer()
    plan = OrganizePlan(
        moves=[
            MoveOperation(
                source_name="photo_001.jpg",
                destination_folder="images",
                reason="image file",
            )
        ],
        summary="move images",
    )
    result = org.execute(plan, tmp_dir, dry_run=True)
    assert result.total_moved == 1
    assert result.dry_run is True
    assert (tmp_dir / "photo_001.jpg").exists(), "dry-run must not touch the filesystem"


def test_execute_moves_file(tmp_dir: Path) -> None:
    org = _make_organizer()
    plan = OrganizePlan(
        moves=[
            MoveOperation(
                source_name="notes.txt",
                destination_folder="text-files",
                reason="text file",
            )
        ],
        summary="move text",
    )
    result = org.execute(plan, tmp_dir, dry_run=False)
    assert result.total_moved == 1
    assert result.total_errors == 0
    assert (tmp_dir / "text-files" / "notes.txt").exists()
    assert not (tmp_dir / "notes.txt").exists()


def test_execute_skips_missing_source(tmp_dir: Path) -> None:
    org = _make_organizer()
    plan = OrganizePlan(
        moves=[
            MoveOperation(
                source_name="nonexistent.txt",
                destination_folder="somewhere",
                reason="missing",
            )
        ],
        summary="",
    )
    result = org.execute(plan, tmp_dir, dry_run=False)
    assert result.total_moved == 0
    assert result.total_skipped == 1


def test_execute_handles_conflict(tmp_dir: Path) -> None:
    (tmp_dir / "dest").mkdir()
    (tmp_dir / "dest" / "photo_001.jpg").write_bytes(b"existing")
    org = _make_organizer()
    plan = OrganizePlan(
        moves=[
            MoveOperation(
                source_name="photo_001.jpg",
                destination_folder="dest",
                reason="image",
            )
        ],
        summary="",
    )
    result = org.execute(plan, tmp_dir, dry_run=False)
    assert result.total_moved == 1
    assert (tmp_dir / "dest" / "photo_001_1.jpg").exists()
