"""Generate a Markdown dependency license inventory from installed metadata.

Run this inside the environment you want to inventory. For release review, use
a clean virtual environment with `pip install .` so dev-only packages are not
mixed into the runtime inventory.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from textwrap import shorten
import tomllib

from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
DEFAULT_OUTPUT = ROOT / "docs" / "legal" / "dependency-license-inventory-2026-06-28.md"
SELECTED_TRANSITIVES = [
    "lxml",
    "playwright",
    "starlette",
    "anyio",
    "httpx",
    "typing-extensions",
]


def main() -> None:
    """Generate the inventory Markdown file."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    direct_names = sorted({Requirement(dep).name for dep in project["dependencies"]})
    rows = [_row_for(name, "direct") for name in direct_names]
    rows.extend(_row_for(name, "selected transitive") for name in SELECTED_TRANSITIVES)
    rows = sorted({row[0].lower(): row for row in rows}.values(), key=lambda row: row[0].lower())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_render(rows), encoding="utf-8")


def _row_for(package_name: str, scope: str) -> tuple[str, str, str, str, str, str]:
    try:
        dist = distribution(package_name)
    except PackageNotFoundError:
        return (package_name, "not installed", scope, "missing", "", "Manual review required.")

    metadata = dist.metadata
    license_text = (metadata.get("License") or "").strip()
    classifiers = metadata.get_all("Classifier") or []
    license_classifiers = [value for value in classifiers if value.startswith("License ::")]
    license_summary = _license_summary(license_text, license_classifiers)
    urls = metadata.get_all("Project-URL") or []
    homepage = metadata.get("Home-page") or ""
    source = homepage or "; ".join(urls[:2])
    if license_summary == "missing":
        note = "Missing license metadata requires manual review."
    elif package_name.lower() == "crawl4ai":
        note = "Upstream attribution tracked in THIRD_PARTY_NOTICES.md."
    elif package_name.lower() == "lxml":
        note = "Also tracked in security audit because of PYSEC-2026-87 via Crawl4AI/lxml."
    else:
        note = ""

    return (
        metadata.get("Name", package_name),
        dist.version,
        scope,
        license_summary,
        source,
        note,
    )


def _license_summary(license_text: str, license_classifiers: list[str]) -> str:
    if license_classifiers:
        return "; ".join(value.removeprefix("License :: ") for value in license_classifiers)
    if license_text:
        return shorten(" ".join(license_text.split()), width=90, placeholder="...")
    return "missing"


def _render(rows: list[tuple[str, str, str, str, str, str]]) -> str:
    lines = [
        "# Scout Dependency License Inventory",
        "",
        "Date: 2026-06-28",
        "Status: Metadata-derived runtime inventory for launch review",
        "",
        "Generated from a clean runtime install of Scout using `pip install .`.",
        "This is a metadata-derived inventory, not legal advice.",
        "Missing license metadata requires manual review against upstream sources before public launch.",
        "",
        "## Known Security/Launch Note",
        "",
        "The dependency audit still reports `PYSEC-2026-87` for `lxml 5.4.0` via the Crawl4AI/lxml dependency path. Public launch remains blocked until that risk is resolved or formally excepted.",
        "",
        "## Inventory",
        "",
        "| Package | Version | Scope | License metadata | Source/Homepage | Notes |",
        "|---|---:|---|---|---|---|",
    ]
    for package, version, scope, license_summary, source, note in rows:
        lines.append(
            f"| {package} | {version} | {scope} | {_cell(license_summary)} | {_cell(source)} | {_cell(note)} |"
        )
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- `direct` means the package is listed in `pyproject.toml` runtime dependencies.",
            "- `selected transitive` means the package is operationally significant for Scout launch review, but this is not a full SBOM.",
            "- This file does not replace legal review, a generated SBOM, or a final release-license decision.",
        ]
    )
    return "\n".join(lines) + "\n"


def _cell(value: str) -> str:
    return value.replace("|", "\\|") if value else ""


if __name__ == "__main__":
    main()
