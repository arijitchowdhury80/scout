"""Tests for Docker distribution files staying aligned with package settings."""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = _ROOT / "docker" / "Dockerfile"
_COMPOSE = _ROOT / "docker" / "docker-compose.yml"
_DOCKERIGNORE = _ROOT / ".dockerignore"


def test_dockerfile_copies_package_metadata_required_for_pip_install() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    metadata_copy = "COPY pyproject.toml README.md LICENSE THIRD_PARTY_NOTICES.md ./"
    assert metadata_copy in dockerfile
    assert "COPY scout/ scout/" in dockerfile
    assert "COPY website/ website/" in dockerfile
    assert dockerfile.index(metadata_copy) < dockerfile.index("RUN pip install --no-cache-dir .")
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
    assert "!LICENSE" in dockerignore
    assert "!THIRD_PARTY_NOTICES.md" in dockerignore


def test_docker_runtime_uses_settings_environment_names() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")
    compose = _COMPOSE.read_text(encoding="utf-8")

    assert "DB_PATH=/data/scout.db" in dockerfile
    assert "SCOUT_DB_PATH" not in dockerfile
    assert "DB_PATH=/data/scout.db" in compose
    assert "SCOUT_DB_PATH" not in compose


def test_dockerfile_runs_as_non_root_user() -> None:
    """FX-13a: prod was verified running the container as uid=0 (root). The
    image must create a fixed-uid non-root user, own /app and /data, and
    switch to it before CMD."""
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    assert "groupadd" in dockerfile and "scoutgroup" in dockerfile
    assert "useradd" in dockerfile and "scoutadmin" in dockerfile
    assert "chown -R" in dockerfile
    assert "USER scoutadmin" in dockerfile

    # USER must land before CMD so the process actually runs unprivileged.
    assert dockerfile.index("USER scoutadmin") < dockerfile.index(
        'CMD ["uvicorn", "scout.api.main:app"'
    )
    # /app and /data must be chowned to the non-root user before the switch.
    chown_idx = dockerfile.index("chown -R")
    assert chown_idx < dockerfile.index("USER scoutadmin")
    chown_line = dockerfile[chown_idx : dockerfile.index("\n", chown_idx)]
    assert "/app" in chown_line
    assert "/data" in chown_line


def test_dockerfile_owns_home_and_crawl4ai_cache_dir_for_non_root_user() -> None:
    """FX: scoutadmin (uid 10001, --no-create-home) has no writable /home
    entry, so crawl4ai's default cache resolution under ~/.crawl4ai
    crash-loops with PermissionError. Prod was live-patched via env vars
    (HOME=/app, CRAWL4AI_BASE_DIRECTORY=/app/.crawl4ai); the Dockerfile must
    own this itself so it doesn't depend on deploy-time env injection."""
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    assert "ENV HOME=/app" in dockerfile
    assert "ENV" in dockerfile and "CRAWL4AI_BASE_DIRECTORY=/app/.crawl4ai" in dockerfile

    home_idx = dockerfile.index("HOME=/app")
    cache_idx = dockerfile.index("CRAWL4AI_BASE_DIRECTORY=/app/.crawl4ai")
    user_idx = dockerfile.index("USER scoutadmin")
    cmd_idx = dockerfile.index('CMD ["uvicorn", "scout.api.main:app"')

    # Both vars must be set before the user switch and before CMD, so the
    # non-root process inherits them for the entire container lifetime.
    assert home_idx < user_idx < cmd_idx
    assert cache_idx < user_idx < cmd_idx

    # /app (which both HOME and the crawl4ai cache dir land under) must be
    # chowned to scoutadmin before the user switch, so it's actually writable.
    chown_idx = dockerfile.index("chown -R")
    chown_line = dockerfile[chown_idx : dockerfile.index("\n", chown_idx)]
    assert "/app" in chown_line
    assert chown_idx < user_idx


def test_published_docker_image_smoke_helper_is_documented() -> None:
    helper = _ROOT / "scripts" / "docker_image_smoke.py"
    policy = (_ROOT / "docs" / "product" / "registry-publishing-policy-2026-06-29.md").read_text(
        encoding="utf-8"
    )
    checklist = (_ROOT / "docs" / "product" / "release-checklist.md").read_text(encoding="utf-8")

    assert helper.exists()
    assert "Smoke-test a published Scout Docker image" in helper.read_text(encoding="utf-8")
    assert "scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG" in policy
    assert "authenticated `/scrape`" in policy
    assert "Helper: `scripts/docker_image_smoke.py`." in checklist
