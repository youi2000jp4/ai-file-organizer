"""Integration-style tests for the CLI layer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from file_organizer.cli import app
from file_organizer.models import MoveOperation, OrganizePlan

runner = CliRunner()


def _mock_plan(moves: list[MoveOperation] | None = None) -> OrganizePlan:
    return OrganizePlan(
        moves=moves or [],
        summary="test plan",
        warnings=[],
    )


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "organize" in result.output.lower() or "usage" in result.output.lower()


def test_organize_no_api_key(tmp_path: Path) -> None:
    with patch("file_organizer.cli.load_config") as mock_cfg:
        cfg = MagicMock()
        cfg.has_api_key.return_value = False
        mock_cfg.return_value = cfg

        result = runner.invoke(app, ["organize", "sort by type", str(tmp_path)])
    assert result.exit_code != 0


def test_organize_empty_directory(tmp_path: Path) -> None:
    with patch("file_organizer.cli.load_config") as mock_cfg:
        cfg = MagicMock()
        cfg.has_api_key.return_value = True
        cfg.max_files = 300
        cfg.exclude_patterns = []
        cfg.confirm_before_execute = False
        mock_cfg.return_value = cfg

        with patch("file_organizer.cli.Organizer") as mock_org:
            instance = mock_org.return_value
            instance.scan_files.return_value = []

            result = runner.invoke(app, ["organize", "sort", str(tmp_path), "--yes"])

    assert result.exit_code == 0
    assert "No files" in result.output


def test_organize_dry_run(tmp_path: Path) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"img")

    with patch("file_organizer.cli.load_config") as mock_cfg:
        cfg = MagicMock()
        cfg.has_api_key.return_value = True
        cfg.max_files = 300
        cfg.exclude_patterns = []
        cfg.confirm_before_execute = False
        mock_cfg.return_value = cfg

        with patch("file_organizer.cli.Organizer") as mock_org:
            from file_organizer.models import FileInfo

            instance = mock_org.return_value
            instance.scan_files.return_value = [
                FileInfo(
                    name="photo.jpg",
                    relative_path="photo.jpg",
                    extension="jpg",
                    size_bytes=3,
                    size_human="3.0 B",
                )
            ]
            plan = _mock_plan(
                [MoveOperation(source_name="photo.jpg", destination_folder="images", reason="jpg")]
            )
            instance.plan = AsyncMock(return_value=plan)
            from file_organizer.models import ExecutionResult

            instance.execute.return_value = ExecutionResult(
                moved=[(tmp_path / "photo.jpg", tmp_path / "images" / "photo.jpg")],
                dry_run=True,
            )

            result = runner.invoke(
                app, ["organize", "move images", str(tmp_path), "--dry-run", "--yes"]
            )

    assert result.exit_code == 0
    assert not (tmp_path / "images" / "photo.jpg").exists()


def test_config_show() -> None:
    with patch("file_organizer.cli.load_config") as mock_cfg:
        cfg = MagicMock()
        cfg.provider = "openai"
        cfg.effective_model = "gpt-4o-mini"
        cfg.max_files = 300
        cfg.confirm_before_execute = True
        cfg.has_api_key.return_value = True
        mock_cfg.return_value = cfg

        result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "openai" in result.output
