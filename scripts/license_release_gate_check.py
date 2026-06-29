#!/usr/bin/env python3
"""Verify Scout license files and package artifacts after license approval."""

from __future__ import annotations

import argparse
import sys
import tarfile
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path


class LicenseGateError(RuntimeError):
    """Raised when the license release gate is not satisfied."""


@dataclass(frozen=True)
class LicenseGateResult:
    """Result of a license gate verification."""

    root: Path
    expected_license: str
    dist_checked: bool


def project_license_expression(pyproject_path: Path) -> str:
    """Return the project license expression from pyproject metadata."""
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    license_value = project.get("license", "")
    if isinstance(license_value, str):
        return license_value
    if isinstance(license_value, dict):
        return str(license_value.get("text", "") or license_value.get("file", ""))
    return ""


def require_contains(path: Path, needle: str) -> None:
    """Require a text file to contain a string."""
    if not path.exists():
        raise LicenseGateError(f"Required file is missing: {path}")
    content = path.read_text(encoding="utf-8", errors="replace")
    if needle not in content:
        raise LicenseGateError(f"{path} does not contain expected text: {needle}")


def verify_source_tree(root: Path, expected_license: str) -> None:
    """Verify source-tree license files and user-facing references."""
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        raise LicenseGateError(f"Missing pyproject.toml at {pyproject}")
    actual_license = project_license_expression(pyproject)
    if actual_license != expected_license:
        raise LicenseGateError(
            f"Expected project license {expected_license!r}, found {actual_license!r}."
        )
    require_contains(root / "LICENSE", expected_license)
    require_contains(root / "README.md", expected_license)
    require_contains(root / "website" / "legal.html", expected_license)
    require_contains(root / "THIRD_PARTY_NOTICES.md", "Crawl4AI")


def verify_dist_artifacts(dist_dir: Path, expected_license: str) -> None:
    """Verify built wheel and sdist include license and notice files."""
    wheel_paths = sorted(dist_dir.glob("scout_web-*.whl"))
    sdist_paths = sorted(dist_dir.glob("scout_web-*.tar.gz"))
    if len(wheel_paths) != 1:
        raise LicenseGateError(
            f"Expected one scout_web wheel in {dist_dir}, found {len(wheel_paths)}."
        )
    if len(sdist_paths) != 1:
        raise LicenseGateError(
            f"Expected one scout_web sdist in {dist_dir}, found {len(sdist_paths)}."
        )
    verify_wheel(wheel_paths[0], expected_license)
    verify_sdist(sdist_paths[0], expected_license)


def verify_wheel(path: Path, expected_license: str) -> None:
    """Verify wheel contents."""
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        license_files = [name for name in names if name.endswith(".dist-info/licenses/LICENSE")]
        metadata_files = [name for name in names if name.endswith(".dist-info/METADATA")]
        if not license_files:
            raise LicenseGateError(f"{path} does not include dist-info/licenses/LICENSE.")
        if not metadata_files:
            raise LicenseGateError(f"{path} does not include dist-info/METADATA.")
        metadata = archive.read(metadata_files[0]).decode("utf-8", errors="replace")
        if f"License-Expression: {expected_license}" not in metadata and (
            f"License: {expected_license}" not in metadata
        ):
            raise LicenseGateError(f"{path} metadata does not declare {expected_license}.")
        if "THIRD_PARTY_NOTICES.md" not in names:
            raise LicenseGateError(f"{path} does not include THIRD_PARTY_NOTICES.md.")


def verify_sdist(path: Path, expected_license: str) -> None:
    """Verify sdist contents."""
    with tarfile.open(path) as archive:
        names = set(archive.getnames())
        if not any(name.endswith("/LICENSE") for name in names):
            raise LicenseGateError(f"{path} does not include LICENSE.")
        if not any(name.endswith("/THIRD_PARTY_NOTICES.md") for name in names):
            raise LicenseGateError(f"{path} does not include THIRD_PARTY_NOTICES.md.")
        pkg_info_names = [name for name in names if name.endswith("/PKG-INFO")]
        if not pkg_info_names:
            raise LicenseGateError(f"{path} does not include PKG-INFO.")
        member = archive.extractfile(pkg_info_names[0])
        if member is None:
            raise LicenseGateError(f"Could not read {pkg_info_names[0]} from {path}.")
        pkg_info = member.read().decode("utf-8", errors="replace")
        if f"License-Expression: {expected_license}" not in pkg_info and (
            f"License: {expected_license}" not in pkg_info
        ):
            raise LicenseGateError(f"{path} metadata does not declare {expected_license}.")


def run_license_gate(
    root: Path,
    expected_license: str,
    dist_dir: Path | None = None,
) -> LicenseGateResult:
    """Run the source and optional artifact license gate."""
    verify_source_tree(root, expected_license)
    if dist_dir is not None:
        verify_dist_artifacts(dist_dir, expected_license)
    return LicenseGateResult(
        root=root, expected_license=expected_license, dist_checked=dist_dir is not None
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Verify Scout license release-gate artifacts.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--expected-license", default="Apache-2.0")
    parser.add_argument("--dist-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the license gate."""
    args = build_parser().parse_args(argv)
    try:
        result = run_license_gate(
            root=args.root,
            expected_license=args.expected_license,
            dist_dir=args.dist_dir,
        )
    except LicenseGateError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print("PASS: Scout license release gate satisfied.")
    print(f"Root: {result.root}")
    print(f"Expected license: {result.expected_license}")
    print(f"Dist checked: {result.dist_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
