from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


SCRIPT_NAMES = [
    "scout-hosted-admin",
    "scout-vps-provision-hosted-key",
    "scout-vps-list-hosted-accounts",
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
            "generate-secret",
            "provision-key",
            "list-accounts",
            "HOSTED_BETA_INVITE_PASSWORD",
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


def test_hosted_admin_generate_secret_outputs_shell_export() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    result = subprocess.run(
        [str(script), "generate-secret", "--label", "HOSTED_ADMIN_TOKEN", "--bytes", "18"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout

    assert "HOSTED_ADMIN_TOKEN=" in output
    assert "export HOSTED_ADMIN_TOKEN=" in output
    assert "openssl rand -base64" not in output
