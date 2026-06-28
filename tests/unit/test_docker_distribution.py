"""Tests for Docker distribution files staying aligned with package settings."""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = _ROOT / "docker" / "Dockerfile"
_COMPOSE = _ROOT / "docker" / "docker-compose.yml"
_DOCKERIGNORE = _ROOT / ".dockerignore"


def test_dockerfile_copies_package_metadata_required_for_pip_install() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    assert "COPY pyproject.toml README.md THIRD_PARTY_NOTICES.md ./" in dockerfile
    assert "COPY scout/ scout/" in dockerfile
    assert "COPY website/ website/" in dockerfile
    assert dockerfile.index("COPY pyproject.toml README.md THIRD_PARTY_NOTICES.md ./") < (
        dockerfile.index("RUN pip install --no-cache-dir .")
    )
    assert dockerfile.index("COPY scout/ scout/") < dockerfile.index(
        "RUN pip install --no-cache-dir ."
    )
    assert dockerfile.index("COPY website/ website/") < dockerfile.index(
        "RUN pip install --no-cache-dir ."
    )


def test_dockerignore_keeps_readme_available_for_package_build() -> None:
    dockerignore = _DOCKERIGNORE.read_text(encoding="utf-8")

    assert "*.md" in dockerignore
    assert "!README.md" in dockerignore
    assert "!THIRD_PARTY_NOTICES.md" in dockerignore


def test_docker_runtime_uses_settings_environment_names() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")
    compose = _COMPOSE.read_text(encoding="utf-8")

    assert "DB_PATH=/data/scout.db" in dockerfile
    assert "SCOUT_DB_PATH" not in dockerfile
    assert "DB_PATH=/data/scout.db" in compose
    assert "SCOUT_DB_PATH" not in compose
