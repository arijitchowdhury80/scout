from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


SCRIPT_NAMES = [
    "scout-hosted-admin",
    "scout-generate-api-key",
    "scout-vps-provision-hosted-key",
    "scout-vps-list-hosted-accounts",
    "scout-vps-list-hosted-usage",
    "scout-vps-list-hosted-purchases",
    "scout-hosted-load-test",
]


def test_vps_admin_scripts_exist_and_are_shell_valid() -> None:
    for script_name in SCRIPT_NAMES:
        script = REPO_ROOT / "scripts" / script_name

        assert script.exists(), f"missing {script_name}"
        assert script.stat().st_mode & 0o111, f"{script_name} is not executable"
        if script.read_text(encoding="utf-8").startswith("#!/usr/bin/env python"):
            subprocess.run([sys.executable, "-m", "py_compile", str(script)], check=True)
        else:
            subprocess.run(["bash", "-n", str(script)], check=True)


def test_vps_admin_scripts_expose_expected_help_and_defaults() -> None:
    expectations = {
        "scout-hosted-admin": [
            "generate-api-key",
            "provision-key",
            "list-accounts",
            "list-usage",
            "list-purchases",
        ],
        "scout-generate-api-key": [
            "Generate and register a Scout hosted API key",
            "--email",
            "scout-hosted-admin generate-api-key",
        ],
        "scout-vps-provision-hosted-key": [
            "scout hosted-provision",
            "--email",
            "--name",
            "--plan",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-vps-list-hosted-accounts": [
            "hosted_tenants",
            "hosted_api_keys",
            "hosted_credit_balances",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-vps-list-hosted-usage": [
            "hosted_credit_ledger",
            "action",
            "credits",
            "standard_balance_after",
            "--summary",
            "credits_spent",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-vps-list-hosted-purchases": [
            "hosted_payment_checkouts",
            "package_id",
            "amount_total_cents",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-hosted-load-test": [
            "--users",
            "250",
            "/v1/hosted/scrape",
            "/v1/hosted/crawl",
            "/v1/hosted/products",
            "/v1/hosted/run/company",
            "/v1/hosted/run/prism",
            "--dry-run",
        ],
    }

    for script_name, expected_fragments in expectations.items():
        script = REPO_ROOT / "scripts" / script_name
        result = subprocess.run(
            [str(script), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr

        for fragment in expected_fragments:
            assert fragment in output


def test_list_accounts_script_never_selects_or_prints_key_hash() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-list-hosted-accounts").read_text()

    assert "docker exec -i scout" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text
    assert "email" in script_text
    assert "name" in script_text
    assert "standard_credits_remaining" in script_text


def test_list_purchases_script_never_prints_raw_keys_or_key_hashes() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-list-hosted-purchases").read_text()

    assert "docker exec -i scout" in script_text
    assert "hosted_payment_checkouts" in script_text
    assert "package_id" in script_text
    assert "amount_total_cents" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text


def test_list_usage_script_never_prints_raw_keys_or_key_hashes() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-list-hosted-usage").read_text()

    assert "docker exec -i scout" in script_text
    assert "hosted_credit_ledger" in script_text
    assert "action" in script_text
    assert "credits" in script_text
    assert "standard_balance_after" in script_text
    assert "credits_spent" in script_text
    assert "--summary" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text


def test_hosted_admin_does_not_expose_password_or_secret_generation() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    result = subprocess.run(
        [str(script), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert "generate-secret" not in output
    assert "generate-password" not in output
    assert "HOSTED_ADMIN_TOKEN" not in output
    assert not (REPO_ROOT / "scripts" / "scout-generate-password").exists()


def test_hosted_admin_has_no_beta_invite_password_flow() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    help_result = subprocess.run(
        [str(script), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    script_text = script.read_text(encoding="utf-8")
    docs_text = (REPO_ROOT / "docs" / "product" / "hosted-admin-operations.md").read_text(
        encoding="utf-8"
    )
    combined = help_result.stdout + help_result.stderr + script_text + docs_text

    assert "HOSTED_BETA_INVITE_PASSWORD" not in combined
    assert "beta invite password" not in combined.lower()
    assert "invite-password" not in combined.lower()
