"""Tests for public package metadata used by local Scout distribution."""

from __future__ import annotations

import tomllib
from pathlib import Path


_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _project_metadata() -> dict:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]


def test_package_metadata_matches_launch_distribution_surface() -> None:
    project = _project_metadata()

    assert project["name"] == "scout-web"
    assert project["readme"] == "README.md"
    assert project["requires-python"] == ">=3.11"
    assert project["scripts"]["scout"] == "scout.cli:app"
    assert project["authors"] == [{"name": "Arijit Chowdhury"}]
    assert "email-validator>=2.0.0" in project["dependencies"]
    assert "Web acquisition" in project["keywords"]
    assert project["urls"]["Homepage"] == "https://github.com/arijitchowdhury80/scout"
    assert project["urls"]["Documentation"] == "https://github.com/arijitchowdhury80/scout#readme"
    assert project["urls"]["Issues"] == "https://github.com/arijitchowdhury80/scout/issues"


def test_package_classifiers_signal_private_beta_python_package() -> None:
    classifiers = set(_project_metadata()["classifiers"])

    assert "Development Status :: 3 - Alpha" in classifiers
    assert "Framework :: FastAPI" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers
    assert "Programming Language :: Python :: 3.13" in classifiers
    assert "Topic :: Internet :: WWW/HTTP :: Indexing/Search" in classifiers


def test_hatch_build_ships_scout_module_when_distribution_name_differs() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))

    assert data["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["scout"]
