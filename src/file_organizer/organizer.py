"""Core file organization logic."""

from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

from rich.console import Console

from .config import Config
from .llm import LLMClient
from .models import ExecutionResult, FileInfo, OrganizePlan

console = Console()

_SIZE_UNITS = ["B", "KB", "MB", "GB", "TB"]


def _human_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in _SIZE_UNITS:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def _matches_any(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _unique_destination(dest: Path) -> Path:
    """Return dest unchanged if it doesn't exist, or dest with a numeric suffix."""
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


class Organizer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.__llm: LLMClient | None = None

    @property
    def _llm(self) -> LLMClient:
        if self.__llm is None:
            self.__llm = LLMClient(self.config)
        return self.__llm

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def scan_files(self, directory: Path, recursive: bool = False) -> list[FileInfo]:
        """Return FileInfo list for files in directory (top-level or recursive)."""
        results: list[FileInfo] = []
        pattern = "**/*" if recursive else "*"

        for path in sorted(directory.glob(pattern)):
            if not path.is_file():
                continue
            if _matches_any(path.name, self.config.exclude_patterns):
                continue
            # Skip hidden files
            if any(part.startswith(".") for part in path.parts[len(directory.parts) :]):
                continue

            rel = path.relative_to(directory)
            results.append(
                FileInfo(
                    name=path.name,
                    relative_path=str(rel),
                    extension=path.suffix.lstrip(".").lower(),
                    size_bytes=path.stat().st_size,
                    size_human=_human_size(path.stat().st_size),
                )
            )

        return results

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    async def plan(
        self,
        instruction: str,
        directory: Path,
        recursive: bool = False,
    ) -> OrganizePlan:
        files = self.scan_files(directory, recursive)
        return await self._llm.plan_organization(instruction, directory, files)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        plan: OrganizePlan,
        directory: Path,
        dry_run: bool = False,
    ) -> ExecutionResult:
        result = ExecutionResult(dry_run=dry_run)

        for op in plan.moves:
            source = directory / op.source_name
            if not source.exists():
                result.skipped.append((source, "source file not found"))
                continue

            dest_dir = directory / op.destination_folder
            dest = _unique_destination(dest_dir / source.name)

            if dry_run:
                result.moved.append((source, dest))
                continue

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                result.moved.append((source, dest))
            except OSError as exc:
                result.errors.append((source, str(exc)))

        return result
