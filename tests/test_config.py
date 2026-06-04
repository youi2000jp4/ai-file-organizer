"""Tests for configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from file_organizer.config import Config


def test_default_config_has_expected_values() -> None:
    cfg = Config(openai_api_key="sk-test")
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4o-mini"
    assert cfg.max_files == 300
    assert cfg.confirm_before_execute is True


def test_has_api_key_true_when_key_set() -> None:
    cfg = Config(openai_api_key="sk-test-key")
    assert cfg.has_api_key() is True


def test_has_api_key_false_when_empty() -> None:
    cfg = Config()
    assert cfg.has_api_key() is False


def test_xai_provider_uses_xai_key() -> None:
    cfg = Config(xai_api_key="xai-key", provider="xai")
    assert cfg.effective_api_key == "xai-key"
    assert "x.ai" in cfg.effective_base_url
    assert "grok" in cfg.effective_model


def test_openai_provider_uses_openai_key() -> None:
    cfg = Config(openai_api_key="sk-key", provider="openai")
    assert cfg.effective_api_key == "sk-key"
    assert "openai.com" in cfg.effective_base_url


def test_env_var_sets_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    cfg = Config()
    assert cfg.openai_api_key == "sk-env-key"
    assert cfg.has_api_key() is True
