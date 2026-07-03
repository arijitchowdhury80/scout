from __future__ import annotations

import json
import runpy
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "scout-stripe-bootstrap-prices"


def test_stripe_bootstrap_dry_run_lists_public_paid_packages_without_secret() -> None:
    result = subprocess.run(
        [str(SCRIPT), "--dry-run", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    package_ids = [package["package_id"] for package in payload["packages"]]

    assert payload["dry_run"] is True
    assert package_ids == ["standard_1000", "standard_3000", "standard_15000"]
    assert "beta_trial" not in package_ids
    assert "browser_100" not in package_ids
    assert payload["packages"][0]["env_key"] == "STRIPE_STANDARD_1000_PRICE_ID"
    assert payload["packages"][0]["amount_cents"] == 1000
    assert "sk_test_" not in result.stdout
    assert "sk_live_" not in result.stdout


def test_stripe_bootstrap_fake_create_outputs_price_env_without_secret(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text("STRIPE_SECRET_KEY=sk_test_not_printed\n", encoding="utf-8")

    result = subprocess.run(
        [
            str(SCRIPT),
            "--secrets-file",
            str(secrets_file),
            "--yes",
            "--fake-stripe",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    created = {item["package_id"]: item["price_id"] for item in payload["created_prices"]}

    assert created == {
        "standard_1000": "price_scout_standard_1000_test",
        "standard_3000": "price_scout_standard_3000_test",
        "standard_15000": "price_scout_standard_15000_test",
    }
    assert "STRIPE_STANDARD_1000_PRICE_ID=price_scout_standard_1000_test" in payload["env_updates"]
    assert "sk_test_not_printed" not in result.stdout


def test_stripe_bootstrap_refuses_live_creation_without_yes(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text("STRIPE_SECRET_KEY=sk_test_not_printed\n", encoding="utf-8")

    result = subprocess.run(
        [str(SCRIPT), "--secrets-file", str(secrets_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "--yes is required" in result.stderr
    assert "sk_test_not_printed" not in result.stderr


def test_stripe_bootstrap_can_update_env_file_with_created_prices(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "STRIPE_SECRET_KEY=sk_test_not_printed",
                "STRIPE_STANDARD_1000_PRICE_ID=",
                "",
            ]
        ),
        encoding="utf-8",
    )
    module = runpy.run_path(str(SCRIPT))

    module["write_price_ids"](
        secrets_file,
        {
            "STRIPE_STANDARD_1000_PRICE_ID": "price_scout_standard_1000_test",
            "STRIPE_STANDARD_3000_PRICE_ID": "price_scout_standard_3000_test",
        },
    )

    updated = secrets_file.read_text(encoding="utf-8")
    assert "HOSTED_BETA_SIGNUP_ENABLED=true" in updated
    assert "STRIPE_STANDARD_1000_PRICE_ID=price_scout_standard_1000_test" in updated
    assert "STRIPE_STANDARD_3000_PRICE_ID=price_scout_standard_3000_test" in updated
    assert "STRIPE_SECRET_KEY=sk_test_not_printed" in updated
