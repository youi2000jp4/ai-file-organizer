"""LLM integration for file-organizer — supports OpenAI and X.AI (Grok)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from .config import Config
from .models import FileInfo, MoveOperation, OrganizePlan

SYSTEM_PROMPT = """\
You are an expert file organization assistant. Given a list of files and a natural language
instruction (which may be in any language including Japanese), determine which files should be
moved and where.

Rules you MUST follow:
1. Only suggest MOVING files — never deleting, renaming, or overwriting.
2. Destination folders are relative to the target directory (e.g. "2026/screenshots").
3. Be CONSERVATIVE — only move files that clearly and confidently match the instruction.
   When in doubt, skip the file.
4. Use lowercase folder names with hyphens for English, natural names for Japanese.
5. Keep folder nesting to 2 levels maximum.
6. Do not move hidden files (starting with ".") or system files unless explicitly instructed.
7. Return a JSON object matching the schema exactly — no extra fields.
"""

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "moves": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_name": {"type": "string"},
                    "destination_folder": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["source_name", "destination_folder", "reason"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["moves", "summary", "warnings"],
    "additionalProperties": False,
}


def _build_user_message(
    instruction: str,
    target_dir: Path,
    files: list[FileInfo],
    max_files: int,
) -> str:
    truncated = len(files) > max_files
    shown = files[:max_files]

    file_lines = "\n".join(
        f"  - {f.relative_path} ({f.size_human})" for f in shown
    )
    truncation_note = (
        f"\n  [Note: showing {max_files} of {len(files)} files — only operate on shown files]\n"
        if truncated
        else ""
    )

    return (
        f"Instruction: {instruction}\n"
        f"Target directory: {target_dir}\n\n"
        f"Files ({len(shown)} shown):\n{file_lines}{truncation_note}"
    )


class LLMClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = AsyncOpenAI(
            api_key=config.effective_api_key,
            base_url=config.effective_base_url,
        )

    async def plan_organization(
        self,
        instruction: str,
        target_dir: Path,
        files: list[FileInfo],
    ) -> OrganizePlan:
        if not files:
            return OrganizePlan(moves=[], summary="No files found to organize.", warnings=[])

        user_message = _build_user_message(
            instruction, target_dir, files, self.config.max_files
        )

        response = await self._client.chat.completions.create(
            model=self.config.effective_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "organize_plan",
                    "strict": True,
                    "schema": RESPONSE_SCHEMA,
                },
            },
            temperature=0.1,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        moves = [MoveOperation(**m) for m in data.get("moves", [])]
        return OrganizePlan(
            moves=moves,
            summary=data.get("summary", ""),
            warnings=data.get("warnings", []),
        )
