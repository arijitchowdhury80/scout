from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


SCRIPT_NAMES = [
    "scout-hosted-admin",
    "scout-validate-hosted-config",
    "scout-write-hosted-config-template",
    "scout-hosted-setup-report",
    "scout-hosted-overview",
    "scout-generate-api-key",
    "scout-vps-provision-hosted-key",
    "scout-vps-list-hosted-accounts",
    "scout-vps-list-hosted-usage",
    "scout-vps-list-hosted-purchases",
    "scout-vps-list-hosted-signups",
    "scout-vps-hosted-metrics",
    "scout-vps-process-pending-beta-signups",
    "scout-vps-retry-failed-beta-signups",
    "scout-vps-send-hosted-test-email",
    "scout-vps-disable-hosted-access",
    "scout-vps-configure-hosted-env",
    "scout-hosted-load-test",
    "scout-stripe-bootstrap-prices",
    "stripe_test_mode_smoke.py",
    "hosted_beta_signup_smoke.py",
    "hosted_production_smoke.py",
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
            "list-signups",
            "metrics",
            "overview",
            "send-test-email",
            "beta-signup-smoke",
            "process-pending-signups",
            "retry-failed-signups",
            "disable-access",
            "readiness",
            "production-smoke",
            "validate-config",
            "write-config-template",
            "setup-report",
            "bootstrap-stripe-prices",
            "stripe-smoke",
            "configure-production-env",
        ],
        "stripe_test_mode_smoke.py": [
            "Verify Scout Stripe test-mode readiness",
            "--base-url",
            "--package-id",
            "--create-checkout",
            "beta_trial",
            "standard_1000",
        ],
        "hosted_production_smoke.py": [
            "Operator smoke gate",
            "--base-url",
            "--json",
            "--require-ready",
        ],
        "hosted_beta_signup_smoke.py": [
            "Smoke-test Scout public beta signup",
            "--base-url",
            "--email",
            "--name",
        ],
        "scout-stripe-bootstrap-prices": [
            "Create Stripe one-time price IDs",
            "--secrets-file",
            "--dry-run",
            "--yes",
            "--write-env",
        ],
        "scout-write-hosted-config-template": [
            "Write a Scout hosted SMTP and Stripe env template",
            "--output",
            "--force",
            "HOSTED_BETA_SIGNUP_ENABLED=true",
            "HOSTED_KEY_DELIVERY_SMTP_HOST=",
            "STRIPE_SECRET_KEY=",
            "STRIPE_WEBHOOK_SECRET=",
        ],
        "scout-hosted-setup-report": [
            "Build a non-secret Scout hosted production setup report",
            "--secrets-file",
            "--base-url",
            "--json",
            "beta_email_delivery",
            "beta_stripe_setup",
            "paid_checkout",
            "scout-hosted-admin configure-production-env",
            "scout-hosted-admin send-test-email",
            "hosted_beta_signup_smoke.py",
        ],
        "scout-hosted-overview": [
            "Show Scout hosted readiness and live metrics",
            "--base-url",
            "hosted_readiness_check.py",
            "scout-vps-hosted-metrics",
        ],
        "scout-validate-hosted-config": [
            "Validate Scout hosted SMTP and Stripe config",
            "--secrets-file",
            "--require",
            "beta",
            "paid",
            "all",
            "HOSTED_KEY_DELIVERY_SMTP_HOST",
            "HOSTED_KEY_DELIVERY_SMTP_USERNAME",
            "HOSTED_KEY_DELIVERY_SMTP_PASSWORD",
            "STRIPE_WEBHOOK_SECRET",
        ],
        "scout-vps-configure-hosted-env": [
            "Configure Scout hosted SMTP and Stripe environment",
            "--secrets-file",
            "--restart",
            "HOSTED_KEY_DELIVERY_SMTP_HOST",
            "STRIPE_SECRET_KEY",
            "/opt/prism/scout/.env",
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
        "scout-vps-list-hosted-signups": [
            "hosted_signup_events",
            "delivery_status",
            "email_beta_registration",
            "--status",
            "--email",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-vps-hosted-metrics": [
            "Scout hosted billing/admin metrics",
            "/v1/billing/admin/metrics",
            "X-API-Key",
            "--format",
            "table",
            "json",
        ],
        "scout-vps-process-pending-beta-signups": [
            "Process queued Scout beta signup requests",
            "--dry-run",
            "--yes",
            "pending_delivery",
            "SmtpHostedApiKeyDeliveryService",
            "HOSTED_KEY_DELIVERY_SMTP_USERNAME",
            "HOSTED_KEY_DELIVERY_SMTP_PASSWORD",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-vps-retry-failed-beta-signups": [
            "Retry failed Scout beta signup deliveries",
            "--dry-run",
            "--yes",
            "failed_signup_requests",
            "admin_failed_beta_delivery_retry",
            "SmtpHostedApiKeyDeliveryService",
            "HOSTED_KEY_DELIVERY_SMTP_USERNAME",
            "HOSTED_KEY_DELIVERY_SMTP_PASSWORD",
            "/data/hosted_accounts.sqlite",
        ],
        "scout-vps-send-hosted-test-email": [
            "Send a Scout hosted API-key delivery smoke-test email",
            "--email",
            "HOSTED_KEY_DELIVERY_SMTP_HOST",
            "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL",
            "HOSTED_KEY_DELIVERY_SMTP_USERNAME",
            "HOSTED_KEY_DELIVERY_SMTP_PASSWORD",
            "No hosted account is created",
            "smoke_test=True",
        ],
        "scout-vps-disable-hosted-access": [
            "Disable Scout hosted access on the VPS",
            "hosted_tenants",
            "hosted_api_keys",
            "--email",
            "--tenant-id",
            "--key-id",
            "--reason",
            "--yes",
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


def test_python_admin_helpers_can_run_from_outside_repo() -> None:
    """VPS invocations may call helper files directly from arbitrary cwd."""
    script = REPO_ROOT / "scripts" / "hosted_production_smoke.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=True,
        capture_output=True,
        cwd="/tmp",
        text=True,
    )

    assert "Operator smoke gate" in result.stdout
    assert "--require-ready" in result.stdout


def test_hosted_config_template_and_vps_config_do_not_request_beta_price_id() -> None:
    """Beta checkout uses Stripe setup mode; no beta price id should be configured."""
    template_text = (REPO_ROOT / "scripts" / "scout-write-hosted-config-template").read_text(
        encoding="utf-8"
    )
    configure_text = (REPO_ROOT / "scripts" / "scout-vps-configure-hosted-env").read_text(
        encoding="utf-8"
    )

    assert "STRIPE_BETA_PRICE_ID" not in template_text
    assert "STRIPE_BETA_PRICE_ID" not in configure_text
    assert "STRIPE_STANDARD_1000_PRICE_ID" in template_text
    assert "STRIPE_STANDARD_1000_PRICE_ID" in configure_text


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


def test_list_signups_script_never_prints_raw_keys_or_key_hashes() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-list-hosted-signups").read_text()

    assert "docker exec -i scout" in script_text
    assert "hosted_signup_events" in script_text
    assert "delivery_status" in script_text
    assert "email_beta_registration" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text


def test_metrics_script_uses_protected_endpoint_without_printing_service_key() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-hosted-metrics").read_text(encoding="utf-8")

    assert "docker exec -i scout" in script_text
    assert "/v1/billing/admin/metrics" in script_text
    assert "SCOUT_API_KEY" in script_text
    assert "X-API-Key" in script_text
    assert "--format" in script_text
    assert "totals" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text
    assert "scout_live_" not in script_text
    assert 'echo "$SCOUT_API_KEY' not in script_text


def test_overview_script_combines_readiness_and_metrics_without_secret_values() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-hosted-overview").read_text(encoding="utf-8")
    admin_text = (REPO_ROOT / "scripts" / "scout-hosted-admin").read_text(encoding="utf-8")

    assert "hosted_readiness_check.py" in script_text
    assert "scout-vps-hosted-metrics" in script_text
    assert "Hosted readiness" in script_text
    assert "Hosted metrics" in script_text
    assert "overview)" in admin_text
    assert "scout-hosted-overview" in admin_text
    assert "SCOUT_API_KEY" not in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text
    assert "scout_live_" not in script_text


def test_send_test_email_script_uses_smoke_mode_and_never_prints_secret_values() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-send-hosted-test-email").read_text()

    assert "docker exec -i scout" in script_text
    assert "SmtpHostedApiKeyDeliveryService" in script_text
    assert "smoke_test=True" in script_text
    assert (
        "requires HOSTED_KEY_DELIVERY_SMTP_HOST, HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL,"
        in script_text
    )
    assert "HOSTED_KEY_DELIVERY_SMTP_USERNAME, and HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "Production hosted delivery also requires" not in script_text
    assert "HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "raw_api_key=''" in script_text
    assert "key_hash" not in script_text
    assert "scout_live_" not in script_text
    assert 'echo "$encoded' not in script_text


def test_process_pending_beta_signups_script_is_confirmed_and_never_prints_secret_values() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-process-pending-beta-signups").read_text(
        encoding="utf-8"
    )

    assert "docker exec -i scout" in script_text
    assert "pending_delivery" in script_text
    assert "pending_signup_requests" in script_text
    assert "SmtpHostedApiKeyDeliveryService" in script_text
    assert (
        "requires HOSTED_KEY_DELIVERY_SMTP_HOST, HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL,"
        in script_text
    )
    assert "HOSTED_KEY_DELIVERY_SMTP_USERNAME, and HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "Production hosted delivery also requires" not in script_text
    assert "--dry-run" in script_text
    assert "--yes" in script_text
    assert "Refusing to process queued beta signups without --yes or --dry-run." in script_text
    assert "HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text
    assert "scout_live_" not in script_text
    assert 'echo "$encoded' not in script_text


def test_retry_failed_beta_signups_script_is_confirmed_and_never_prints_secret_values() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-retry-failed-beta-signups").read_text(
        encoding="utf-8"
    )
    admin_text = (REPO_ROOT / "scripts" / "scout-hosted-admin").read_text(encoding="utf-8")

    assert "docker exec -i scout" in script_text
    assert "failed_signup_requests" in script_text
    assert "admin_failed_beta_delivery_retry" in script_text
    assert "SmtpHostedApiKeyDeliveryService" in script_text
    assert (
        "requires HOSTED_KEY_DELIVERY_SMTP_HOST, HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL,"
        in script_text
    )
    assert "HOSTED_KEY_DELIVERY_SMTP_USERNAME, and HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "--dry-run" in script_text
    assert "--yes" in script_text
    assert "Refusing to retry failed beta signups without --yes or --dry-run." in script_text
    assert "retry-failed-signups)" in admin_text
    assert "scout-vps-retry-failed-beta-signups" in admin_text
    assert "HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text
    assert "scout_live_" not in script_text
    assert 'echo "$encoded' not in script_text


def test_disable_access_script_is_confirmed_and_never_prints_secret_values() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-disable-hosted-access").read_text(
        encoding="utf-8"
    )

    assert "docker exec -i scout" in script_text
    assert "hosted_tenants" in script_text
    assert "hosted_api_keys" in script_text
    assert "UPDATE hosted_tenants SET status = 'disabled'" in script_text
    assert "UPDATE hosted_api_keys SET status = 'disabled'" in script_text
    assert "--yes" in script_text
    assert "Refusing to mutate hosted access without --yes." in script_text
    assert "key_hash" not in script_text
    assert "raw_api_key" not in script_text
    assert 'echo "$encoded' not in script_text


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


def test_hosted_admin_readiness_command_wraps_readiness_checker() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    result = subprocess.run(
        [str(script), "readiness", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    script_text = script.read_text(encoding="utf-8")

    assert "--base-url" in output
    assert "--require-beta-signup" in output
    assert "--require-paid-checkout" in output
    assert "--json" in output
    assert "hosted_readiness_check.py" in script_text


def test_hosted_admin_validate_config_command_wraps_validator() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    result = subprocess.run(
        [str(script), "validate-config", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    script_text = script.read_text(encoding="utf-8")

    assert "--secrets-file" in output
    assert "--require" in output
    assert "scout-validate-hosted-config" in script_text


def test_hosted_admin_write_config_template_command_wraps_template_writer() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    result = subprocess.run(
        [str(script), "write-config-template", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    script_text = script.read_text(encoding="utf-8")

    assert "--output" in output
    assert "--force" in output
    assert "scout-write-hosted-config-template" in script_text


def test_hosted_admin_setup_report_command_wraps_setup_report() -> None:
    script = REPO_ROOT / "scripts" / "scout-hosted-admin"
    result = subprocess.run(
        [str(script), "setup-report", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    script_text = script.read_text(encoding="utf-8")

    assert "--secrets-file" in output
    assert "--base-url" in output
    assert "--json" in output
    assert "scout-hosted-setup-report" in script_text


def test_hosted_setup_report_groups_missing_operator_work_without_secret_values(
    tmp_path: Path,
) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "STRIPE_PORTAL_RETURN_URL=https://scout.chowmes.com/account",
                "STRIPE_SECRET_KEY=sk_test_should_not_print",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-hosted-setup-report"),
            "--secrets-file",
            str(secrets_file),
            "--base-url",
            "https://scout.chowmes.com",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 2
    assert "Scout hosted production setup report" in output
    assert "beta_email_delivery: blocked" in output
    assert "beta_stripe_setup: blocked" in output
    assert "paid_checkout: blocked" in output
    assert "HOSTED_KEY_DELIVERY_SMTP_HOST" in output
    assert "STRIPE_WEBHOOK_SECRET" in output
    assert "scout-hosted-admin configure-production-env" in output
    assert "scout-hosted-admin send-test-email" in output
    assert "hosted_beta_signup_smoke.py" in output
    assert "sk_test_should_not_print" not in output


def test_hosted_setup_report_json_never_prints_secret_values(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com",
                "HOSTED_KEY_DELIVERY_SMTP_PORT=587",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_USERNAME=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_PASSWORD=smtp-secret-value",
                "STRIPE_SECRET_KEY=sk_test_should_not_print",
                "STRIPE_STANDARD_1000_PRICE_ID=price_1000",
                "STRIPE_STANDARD_3000_PRICE_ID=price_3000",
                "STRIPE_STANDARD_15000_PRICE_ID=price_15000",
                "STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success",
                "STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled",
                "STRIPE_PORTAL_RETURN_URL=https://scout.chowmes.com/account",
                "STRIPE_WEBHOOK_SECRET=whsec_should_not_print",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-hosted-setup-report"),
            "--secrets-file",
            str(secrets_file),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert '"capability": "beta_email_delivery"' in output
    assert '"status": "configured"' in output
    assert '"capability": "paid_checkout"' in output
    assert "smtp-secret-value" not in output
    assert "sk_test_should_not_print" not in output
    assert "whsec_should_not_print" not in output


def test_write_hosted_config_template_creates_non_secret_template(tmp_path: Path) -> None:
    output = tmp_path / "scout-production.env"
    script = REPO_ROOT / "scripts" / "scout-write-hosted-config-template"

    result = subprocess.run(
        [str(script), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    text = output.read_text(encoding="utf-8")
    assert "Wrote hosted config template" in result.stdout
    assert "HOSTED_BETA_SIGNUP_ENABLED=true" in text
    assert "HOSTED_BETA_SIGNUP_RATE_LIMIT_MAX_REQUESTS=3" in text
    assert "HOSTED_BETA_SIGNUP_RATE_LIMIT_WINDOW_SECONDS=3600" in text
    assert "HOSTED_KEY_DELIVERY_SMTP_HOST=" in text
    assert 'HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL="Arijit Chowdhury <scout@chowmes.com>"' in text
    assert "STRIPE_SECRET_KEY=" in text
    assert "STRIPE_WEBHOOK_SECRET=" in text
    assert "sk_test_" not in text
    assert "sk_live_" not in text
    assert "whsec_" not in text
    assert "smtp-secret" not in text


def test_configure_hosted_env_allowlists_beta_signup_rate_limit_settings() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-configure-hosted-env").read_text(
        encoding="utf-8"
    )

    assert "HOSTED_BETA_SIGNUP_RATE_LIMIT_MAX_REQUESTS" in script_text
    assert "HOSTED_BETA_SIGNUP_RATE_LIMIT_WINDOW_SECONDS" in script_text


def test_configure_hosted_env_restart_rebuilds_container_before_health_check() -> None:
    """Hosted env restarts must not reuse a stale Scout image after code deploys."""
    script_text = (REPO_ROOT / "scripts" / "scout-vps-configure-hosted-env").read_text(
        encoding="utf-8"
    )

    assert (
        "docker compose -f docker/docker-compose.yml up -d --build --force-recreate scout"
        in script_text
    )
    assert "docker inspect --format='{{.State.Health.Status}}' scout" in script_text


def test_write_hosted_config_template_refuses_overwrite_without_force(tmp_path: Path) -> None:
    output = tmp_path / "scout-production.env"
    output.write_text("EXISTING=1\n", encoding="utf-8")
    script = REPO_ROOT / "scripts" / "scout-write-hosted-config-template"

    result = subprocess.run(
        [str(script), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert output.read_text(encoding="utf-8") == "EXISTING=1\n"


def test_validate_hosted_config_reports_missing_required_keys_without_secret_values(
    tmp_path: Path,
) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "STRIPE_SECRET_KEY=sk_test_should_not_print",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-validate-hosted-config"),
            "--secrets-file",
            str(secrets_file),
            "--require",
            "paid",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 2
    assert "Missing required hosted config keys" in output
    assert "STRIPE_WEBHOOK_SECRET" in output
    assert "STRIPE_STANDARD_1000_PRICE_ID" in output
    assert "STRIPE_STANDARD_3000_PRICE_ID" in output
    assert "STRIPE_STANDARD_15000_PRICE_ID" in output
    assert "sk_test_should_not_print" not in output


def test_validate_hosted_config_requires_smtp_credentials_for_beta(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com",
                "HOSTED_KEY_DELIVERY_SMTP_PORT=587",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-validate-hosted-config"),
            "--secrets-file",
            str(secrets_file),
            "--require",
            "beta",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 2
    assert "HOSTED_KEY_DELIVERY_SMTP_USERNAME" in output
    assert "HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in output


def test_validate_hosted_config_accepts_complete_beta_and_paid_config(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com",
                "HOSTED_KEY_DELIVERY_SMTP_PORT=587",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_USERNAME=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_PASSWORD=smtp-secret-value",
                "HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true",
                "STRIPE_SECRET_KEY=sk_test_should_not_print",
                "STRIPE_STANDARD_1000_PRICE_ID=price_1000",
                "STRIPE_STANDARD_3000_PRICE_ID=price_3000",
                "STRIPE_STANDARD_15000_PRICE_ID=price_15000",
                "STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success",
                "STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled",
                "STRIPE_BETA_SUCCESS_URL=https://scout.chowmes.com/beta?checkout=success",
                "STRIPE_BETA_CANCEL_URL=https://scout.chowmes.com/beta?checkout=cancelled",
                "STRIPE_PORTAL_RETURN_URL=https://scout.chowmes.com/account",
                "STRIPE_WEBHOOK_SECRET=whsec_should_not_print",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-validate-hosted-config"),
            "--secrets-file",
            str(secrets_file),
            "--require",
            "all",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert "Hosted config validation passed for: all" in output
    assert "HOSTED_KEY_DELIVERY_SMTP_HOST" in output
    assert "STRIPE_WEBHOOK_SECRET" in output
    assert "smtp-secret-value" not in output
    assert "sk_test_should_not_print" not in output
    assert "whsec_should_not_print" not in output


def test_validate_hosted_config_warns_on_non_https_beta_redirects(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com",
                "HOSTED_KEY_DELIVERY_SMTP_PORT=587",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_USERNAME=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_PASSWORD=smtp-secret-value",
                "STRIPE_SECRET_KEY=sk_test_should_not_print",
                "STRIPE_STANDARD_1000_PRICE_ID=price_1000",
                "STRIPE_STANDARD_3000_PRICE_ID=price_3000",
                "STRIPE_STANDARD_15000_PRICE_ID=price_15000",
                "STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success",
                "STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled",
                "STRIPE_BETA_SUCCESS_URL=http://127.0.0.1/beta?checkout=success",
                "STRIPE_BETA_CANCEL_URL=http://127.0.0.1/beta?checkout=cancelled",
                "STRIPE_PORTAL_RETURN_URL=https://scout.chowmes.com/account",
                "STRIPE_WEBHOOK_SECRET=whsec_should_not_print",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-validate-hosted-config"),
            "--secrets-file",
            str(secrets_file),
            "--require",
            "all",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 2
    assert "STRIPE_BETA_SUCCESS_URL should use https:// for hosted production." in output
    assert "STRIPE_BETA_CANCEL_URL should use https:// for hosted production." in output
    assert "smtp-secret-value" not in output
    assert "sk_test_should_not_print" not in output
    assert "whsec_should_not_print" not in output


def test_validate_hosted_config_rejects_obsolete_beta_price_id(tmp_path: Path) -> None:
    secrets_file = tmp_path / "scout-production.env"
    secrets_file.write_text(
        "\n".join(
            [
                "HOSTED_BETA_SIGNUP_ENABLED=true",
                "HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.example.com",
                "HOSTED_KEY_DELIVERY_SMTP_PORT=587",
                "HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_USERNAME=scout@chowmes.com",
                "HOSTED_KEY_DELIVERY_SMTP_PASSWORD=smtp-secret-value",
                "STRIPE_SECRET_KEY=sk_test_should_not_print",
                "STRIPE_BETA_PRICE_ID=price_obsolete_should_not_print",
                "STRIPE_STANDARD_1000_PRICE_ID=price_1000",
                "STRIPE_STANDARD_3000_PRICE_ID=price_3000",
                "STRIPE_STANDARD_15000_PRICE_ID=price_15000",
                "STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success",
                "STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled",
                "STRIPE_PORTAL_RETURN_URL=https://scout.chowmes.com/account",
                "STRIPE_WEBHOOK_SECRET=whsec_should_not_print",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "scout-validate-hosted-config"),
            "--secrets-file",
            str(secrets_file),
            "--require",
            "all",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 2
    assert "STRIPE_BETA_PRICE_ID is obsolete" in output
    assert "price_obsolete_should_not_print" not in output
    assert "smtp-secret-value" not in output
    assert "sk_test_should_not_print" not in output
    assert "whsec_should_not_print" not in output


def test_configure_hosted_env_uses_allowlist_and_never_echoes_secret_values() -> None:
    script_text = (REPO_ROOT / "scripts" / "scout-vps-configure-hosted-env").read_text(
        encoding="utf-8"
    )

    assert "ALLOWED_KEYS" in script_text
    assert "HOSTED_KEY_DELIVERY_SMTP_HOST" in script_text
    assert "HOSTED_KEY_DELIVERY_SMTP_PASSWORD" in script_text
    assert "STRIPE_SECRET_KEY" in script_text
    assert "STRIPE_WEBHOOK_SECRET" in script_text
    assert "STRIPE_STANDARD_1000_PRICE_ID" in script_text
    assert "STRIPE_STANDARD_3000_PRICE_ID" in script_text
    assert "STRIPE_STANDARD_15000_PRICE_ID" in script_text
    assert "STRIPE_BETA_SUCCESS_URL" in script_text
    assert "STRIPE_BETA_CANCEL_URL" in script_text
    assert "STRIPE_PORTAL_RETURN_URL" in script_text
    assert "scout-validate-hosted-config" in script_text
    assert "--require" in script_text
    assert "SCOUT_API_KEY" not in script_text
    assert "preserved_lines" in script_text
    assert "updated_keys" in script_text
    assert 'cat "$secrets_file"' not in script_text
    assert 'echo "$encoded' not in script_text
