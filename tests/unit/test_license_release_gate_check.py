from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts import license_release_gate_check


def _write_source_tree(root: Path, license_text: str = "Apache-2.0") -> None:
    (root / "website").mkdir()
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "scout-web"\nlicense = "{license_text}"\n',
        encoding="utf-8",
    )
    (root / "LICENSE").write_text(f"Scout license: {license_text}\n", encoding="utf-8")
    (root / "README.md").write_text(f"License: {license_text}\n", encoding="utf-8")
    (root / "website" / "legal.html").write_text(f"License: {license_text}\n", encoding="utf-8")
    (root / "THIRD_PARTY_NOTICES.md").write_text("Crawl4AI\n", encoding="utf-8")


def test_license_gate_passes_for_source_tree_with_expected_license(tmp_path: Path) -> None:
    _write_source_tree(tmp_path)

    result = license_release_gate_check.run_license_gate(tmp_path, "Apache-2.0")

    assert result.expected_license == "Apache-2.0"
    assert result.dist_checked is False


def test_license_gate_accepts_canonical_apache_license_file(tmp_path: Path) -> None:
    _write_source_tree(tmp_path)
    (tmp_path / "LICENSE").write_text(
        "Apache License\nVersion 2.0, January 2004\n", encoding="utf-8"
    )

    result = license_release_gate_check.run_license_gate(tmp_path, "Apache-2.0")

    assert result.expected_license == "Apache-2.0"


def test_license_gate_fails_when_pyproject_license_is_missing(tmp_path: Path) -> None:
    _write_source_tree(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "scout-web"\n', encoding="utf-8")

    with pytest.raises(
        license_release_gate_check.LicenseGateError, match="Expected project license"
    ):
        license_release_gate_check.run_license_gate(tmp_path, "Apache-2.0")


def test_license_gate_verifies_wheel_and_sdist_metadata(tmp_path: Path) -> None:
    _write_source_tree(tmp_path)
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "scout_web-0.1.0-py3-none-any.whl"
    sdist = dist / "scout_web-0.1.0.tar.gz"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("scout_web-0.1.0.dist-info/licenses/LICENSE", "Apache-2.0\n")
        archive.writestr("scout_web-0.1.0.dist-info/METADATA", "License-Expression: Apache-2.0\n")
        archive.writestr("THIRD_PARTY_NOTICES.md", "Crawl4AI\n")
    with tarfile.open(sdist, "w:gz") as archive:
        for name, content in {
            "scout_web-0.1.0/LICENSE": "Apache-2.0\n",
            "scout_web-0.1.0/THIRD_PARTY_NOTICES.md": "Crawl4AI\n",
            "scout_web-0.1.0/PKG-INFO": "License-Expression: Apache-2.0\n",
        }.items():
            file_path = tmp_path / name.replace("/", "_")
            file_path.write_text(content, encoding="utf-8")
            archive.add(file_path, arcname=name)

    result = license_release_gate_check.run_license_gate(tmp_path, "Apache-2.0", dist)

    assert result.dist_checked is True


def test_license_gate_main_reports_failure_for_current_unlicensed_tree(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = license_release_gate_check.main(["--root", "/path/that/does/not/exist"])

    assert exit_code == 2
    assert "FAIL" in capsys.readouterr().err
