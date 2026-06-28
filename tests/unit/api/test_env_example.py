"""Tests that public env examples stay aligned with Scout settings."""

from __future__ import annotations

from pathlib import Path

from scout.api.config import Settings


_ENV_EXAMPLE = Path(__file__).resolve().parents[3] / ".env.example"


def test_env_example_documents_all_non_secret_setting_names() -> None:
    env_text = _ENV_EXAMPLE.read_text(encoding="utf-8")

    for field_name in Settings.model_fields:
        env_name = field_name.upper()
        assert f"{env_name}=" in env_text, f"{env_name} missing from .env.example"
