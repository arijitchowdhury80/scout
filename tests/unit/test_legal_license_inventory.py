"""Tests for the committed dependency license inventory."""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_INVENTORY = _ROOT / "docs" / "legal" / "dependency-license-inventory-2026-06-28.md"
_CHECKLIST = _ROOT / "docs" / "legal" / "legal-readiness-checklist.md"
_RELEASE_CHECKLIST = _ROOT / "docs" / "product" / "release-checklist.md"


def test_dependency_license_inventory_exists_with_required_scope_notes() -> None:
    inventory = _INVENTORY.read_text(encoding="utf-8")

    assert "# Scout Dependency License Inventory" in inventory
    assert "Generated from a clean runtime install of Scout" in inventory
    assert "metadata-derived inventory, not legal advice" in inventory
    assert "Missing license metadata requires manual review" in inventory


def test_dependency_license_inventory_covers_runtime_dependencies() -> None:
    inventory = _INVENTORY.read_text(encoding="utf-8")
    normalized_inventory = inventory.lower()

    for package in [
        "crawl4ai",
        "fastapi",
        "uvicorn",
        "pydantic",
        "algoliasearch",
        "playwright",
        "lxml",
    ]:
        assert f"| {package} |" in normalized_inventory

    assert "PYSEC-2026-87" in inventory
    assert "Crawl4AI/lxml" in inventory


def test_legal_checklists_link_dependency_license_inventory() -> None:
    checklist = _CHECKLIST.read_text(encoding="utf-8")
    release_checklist = _RELEASE_CHECKLIST.read_text(encoding="utf-8")

    assert "- [x] Generate a dependency license inventory before public launch." in checklist
    assert "dependency-license-inventory-2026-06-28.md" in checklist
    assert "Dependency license inventory generated." in release_checklist
    assert "dependency-license-inventory-2026-06-28.md" in release_checklist
