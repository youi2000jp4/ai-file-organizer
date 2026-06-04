"""Data models for file-organizer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Metadata about a single file."""

    name: str
    relative_path: str
    extension: str
    size_bytes: int
    size_human: str


class MoveOperation(BaseModel):
    """A single planned file move."""

    source_name: str = Field(description="File name (relative path from target dir)")
    destination_folder: str = Field(description="Destination folder relative to target dir")
    reason: str = Field(description="Why this file matches the instruction")


class OrganizePlan(BaseModel):
    """Full organization plan returned by the LLM."""

    moves: list[MoveOperation] = Field(default_factory=list)
    summary: str = Field(description="Human-readable summary of the plan")
    warnings: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Result of executing an organization plan."""

    moved: list[tuple[Path, Path]] = Field(default_factory=list)
    skipped: list[tuple[Path, str]] = Field(default_factory=list)
    errors: list[tuple[Path, str]] = Field(default_factory=list)
    dry_run: bool = False

    @property
    def total_moved(self) -> int:
        return len(self.moved)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)

    @property
    def total_errors(self) -> int:
        return len(self.errors)
