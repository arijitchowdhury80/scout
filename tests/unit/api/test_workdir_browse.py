from pathlib import Path
from subprocess import CompletedProcess

from fastapi.testclient import TestClient
import pytest

from scout.api.main import app
from scout.api.routers import workdir


_HEADERS = {"X-API-Key": "dev-key"}


def test_workdir_browse_requires_auth(tmp_path: Path) -> None:
    client = TestClient(app)

    resp = client.get("/workdir/browse", params={"path": str(tmp_path)})

    assert resp.status_code == 403


def test_workdir_browse_lists_child_directories_sorted(tmp_path: Path) -> None:
    (tmp_path / "zeta").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "notes.txt").write_text("not a folder", encoding="utf-8")
    client = TestClient(app)

    resp = client.get("/workdir/browse", params={"path": str(tmp_path)}, headers=_HEADERS)

    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == str(tmp_path.resolve())
    assert data["parent"] == str(tmp_path.resolve().parent)
    assert [entry["name"] for entry in data["directories"]] == ["alpha", "zeta"]
    assert all(entry["is_dir"] for entry in data["directories"])


def test_workdir_browse_rejects_non_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "records.json"
    file_path.write_text("{}", encoding="utf-8")
    client = TestClient(app)

    resp = client.get("/workdir/browse", params={"path": str(file_path)}, headers=_HEADERS)

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Path is not a directory"


def test_native_workdir_picker_returns_selected_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    selected = tmp_path / "chosen"
    selected.mkdir()

    def fake_run(*args: object, **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(args=args, returncode=0, stdout=f"{selected}\n", stderr="")

    monkeypatch.setattr(workdir.subprocess, "run", fake_run)
    client = TestClient(app)

    resp = client.post(
        "/workdir/pick-native",
        headers=_HEADERS,
        json={"current_path": str(tmp_path)},
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "path": str(selected),
        "picked": True,
        "cancelled": False,
        "reason": "",
    }


def test_native_workdir_picker_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOUT_DISABLE_NATIVE_PICKER", "1")
    client = TestClient(app)

    resp = client.post("/workdir/pick-native", headers=_HEADERS, json={})

    assert resp.status_code == 200
    assert resp.json() == {
        "path": "",
        "picked": False,
        "cancelled": False,
        "reason": "disabled",
    }


def test_native_workdir_picker_cancel_does_not_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*args: object, **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(args=args, returncode=1, stdout="", stderr="User canceled.")

    monkeypatch.setattr(workdir.subprocess, "run", fake_run)
    client = TestClient(app)

    resp = client.post(
        "/workdir/pick-native",
        headers=_HEADERS,
        json={"current_path": str(tmp_path)},
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "path": "",
        "picked": False,
        "cancelled": True,
        "reason": "cancelled",
    }
