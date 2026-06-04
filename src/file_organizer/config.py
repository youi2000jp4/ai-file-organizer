"""Configuration management for file-organizer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]
import tomli_w
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path.home() / ".config" / "file-organizer"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_EXCLUDE_PATTERNS = [
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".git",
    ".gitignore",
    "__pycache__",
    "*.pyc",
    "node_modules",
]


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FILE_ORGANIZER_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    # LLM provider settings
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-4o-mini")

    # Grok / X.AI alternative
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    provider: Literal["openai", "xai"] = Field(default="openai")

    # Behavior settings
    max_files: int = Field(default=300, ge=1, le=5000)
    exclude_patterns: list[str] = Field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS.copy())
    confirm_before_execute: bool = Field(default=True)
    create_backup: bool = Field(default=False)

    @field_validator("openai_api_key", "xai_api_key", mode="before")
    @classmethod
    def empty_string_for_none(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v)

    @property
    def effective_api_key(self) -> str:
        if self.provider == "xai":
            return self.xai_api_key
        return self.openai_api_key

    @property
    def effective_base_url(self) -> str:
        if self.provider == "xai":
            return "https://api.x.ai/v1"
        return self.openai_base_url

    @property
    def effective_model(self) -> str:
        if self.provider == "xai":
            return "grok-3-mini"
        return self.model

    def has_api_key(self) -> bool:
        return bool(self.effective_api_key)


def load_config() -> Config:
    """Load config from file and environment variables."""
    overrides: dict[str, Any] = {}

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            file_data = tomllib.load(f)
        overrides.update(file_data)

    # Also check for local .file-organizer.toml
    local_config = Path(".file-organizer.toml")
    if local_config.exists():
        with open(local_config, "rb") as f:
            local_data = tomllib.load(f)
        overrides.update(local_data)

    return Config(**overrides)


def save_config(config: Config) -> None:
    """Persist config to TOML file (excludes secrets)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "model": config.model,
        "provider": config.provider,
        "max_files": config.max_files,
        "confirm_before_execute": config.confirm_before_execute,
        "create_backup": config.create_backup,
        "exclude_patterns": config.exclude_patterns,
    }
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)


def set_api_key(key: str, provider: Literal["openai", "xai"] = "openai") -> None:
    """Store API key in the OS environment config file (not TOML — never persist secrets)."""
    env_var = "OPENAI_API_KEY" if provider == "openai" else "XAI_API_KEY"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    env_file = CONFIG_DIR / ".env"
    lines: list[str] = []
    if env_file.exists():
        lines = env_file.read_text().splitlines()
    new_lines = [ln for ln in lines if not ln.startswith(f"{env_var}=")]
    new_lines.append(f"{env_var}={key}")
    env_file.write_text("\n".join(new_lines) + "\n")
    env_file.chmod(0o600)
