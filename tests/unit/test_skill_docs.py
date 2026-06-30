from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_skill_readme_uses_verified_private_beta_install_path() -> None:
    readme = _read("scout/skill/README.md")

    assert "Scout Skill Wrapper" in readme
    assert (
        'pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"'
        in readme
    )
    assert "pip install git+https://github.com/arijitchowdhury80/scout.git\n" not in readme
    assert "pip install scout-web" in readme
    assert "reserved for after the license and" in readme
    assert "publishing gates close" in readme


def test_skill_playbook_matches_current_launch_surface_and_auth_boundary() -> None:
    skill = _read("scout/skill/scout.md")

    assert "Public launch/docs routes are intentionally unauthenticated" in skill
    for path in [
        "/quickstart",
        "/pricing",
        "/beta",
        "/docs",
        "/openapi.json",
        "/third-party-notices",
    ]:
        assert path in skill
    for path in ["/scrape", "/crawl", "/products", "/run/{use_case}", "/runs/{run_id}"]:
        assert path in skill
    assert "previous experimental local" in skill
    assert "removed from the supported product surface" in skill
    assert "hosted API, and artifact examples" in skill
    assert "hosted API" in skill
    assert "All HTTP endpoints except `/` and `/health` require" not in skill


def test_skill_usage_verification_records_package_smoke() -> None:
    verification = _read("docs/product/skill-usage-verification-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Skill Usage Verification" in verification
    assert "passed from the current built package" in verification
    assert "skill_exists: True" in verification
    assert "readme_exists: True" in verification
    assert "installed CLI contains: run, products, hosted-provision, serve" in verification
    assert "company / Adobe" in verification
    assert "careers / Algolia" in verification
    assert "PRISM / Nike" in verification
    assert "records: 1" in verification
    assert "citations: 1" in verification
    assert "artifacts_exist: true" in verification
    assert "Stale skill docs were corrected" in checklist
    assert "- [x] Skill usage docs tested from current package." in checklist
    assert "docs/product/skill-usage-verification-2026-06-29.md" in checklist
