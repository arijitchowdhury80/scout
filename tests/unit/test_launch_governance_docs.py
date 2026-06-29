from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_policy_defines_private_reporting_and_supported_scope() -> None:
    policy = _read("SECURITY.md")

    assert "Private Beta Security Policy" in policy
    assert "Do not open a public GitHub issue for security reports" in policy
    assert "Supported Versions" in policy
    assert "Hosted Scout" in policy
    assert "Local Scout" in policy
    assert "Security Review Checklist" in policy
    assert "SSRF" in policy
    assert "API key" in policy
    assert "secrets" in policy.lower()


def test_private_beta_issue_templates_exist_and_route_feedback() -> None:
    bug_report = ROOT / ".github" / "ISSUE_TEMPLATE" / "private_beta_bug.yml"
    feature_request = ROOT / ".github" / "ISSUE_TEMPLATE" / "private_beta_feature.yml"

    for template in [bug_report, feature_request]:
        assert template.exists()
        parsed = yaml.safe_load(template.read_text(encoding="utf-8"))
        assert parsed["labels"]
        assert any("private-beta" in label for label in parsed["labels"])
        assert parsed["body"]

    bug_template = yaml.safe_load(bug_report.read_text(encoding="utf-8"))
    feature_template = yaml.safe_load(feature_request.read_text(encoding="utf-8"))

    bug_text = bug_report.read_text(encoding="utf-8")
    assert bug_template["name"] == "Private beta bug"
    assert "Scout version" in bug_text
    assert "Local package, Docker, hosted API, or skill" in bug_text
    assert "Logs, run ID, or artifact path" in bug_text

    feature_text = feature_request.read_text(encoding="utf-8")
    assert feature_template["name"] == "Private beta feature request"
    assert "Product, company intel, hosted API, local CLI, or distribution" in feature_text
    assert "What workflow are you trying to complete?" in feature_text


def test_private_beta_support_and_onboarding_playbook_closes_beta_ops_gates() -> None:
    playbook = _read("docs/product/private-beta-onboarding-and-support.md")
    checklist = _read("docs/product/release-checklist.md")
    launch_plan = _read("docs/product/private-beta-launch-plan.md")

    assert "Private Beta Onboarding And Support" in playbook
    assert "GitHub issue templates" in playbook
    assert ".github/ISSUE_TEMPLATE/private_beta_bug.yml" in playbook
    assert ".github/ISSUE_TEMPLATE/private_beta_feature.yml" in playbook
    assert "Security reports must not be filed as public GitHub issues" in playbook
    assert "Best-effort private beta targets" in playbook
    assert "Hosted key/payment access issue" in playbook
    assert "Choose A Path" in playbook
    assert "Local package" in playbook
    assert "Docker" in playbook
    assert "Hosted beta" in playbook
    assert "Skill" in playbook
    assert "pip install" in playbook
    assert "/v1/hosted/me" in playbook
    assert "/v1/hosted/scrape" in playbook
    assert "source_pages.json" in playbook
    assert "extraction_report.md" in playbook
    assert "Do not include" in playbook
    assert "API keys" in playbook
    assert "cookies" in playbook
    assert "private customer data" in playbook
    assert "- [x] Support contact/channel confirmed." in checklist
    assert "- [x] Beta tester onboarding instructions verified." in checklist
    assert "docs/product/private-beta-onboarding-and-support.md" in checklist
    assert "Add private beta support channel and onboarding guide" in launch_plan
    assert "private beta issue templates" in launch_plan


def test_private_beta_launch_plan_reflects_current_evidence_and_boundaries() -> None:
    launch_plan = _read("docs/product/private-beta-launch-plan.md")

    assert "Controlled private beta plan; public launch remains blocked" in launch_plan
    assert "docs/product/launch-evidence-index-2026-06-29.md" in launch_plan
    assert "docs/product/launch-decision-dashboard-2026-06-29.md" in launch_plan
    assert "docs/product/launch-gate-burndown-2026-06-29.md" in launch_plan
    assert "docs/product/launch-decision-request-2026-06-29.md" in launch_plan
    assert (
        "URL or captured page -> evidence ledger -> typed records -> portable artifacts"
        in launch_plan
    )
    assert 'The beta promise is not "scrape anything."' in launch_plan

    verified_surfaces = [
        "Local branch-qualified install",
        "Docker built from source",
        "Hosted API for approved testers",
        "Claude/Codex skill docs",
        "Launch website",
    ]
    for surface in verified_surfaces:
        assert surface in launch_plan

    current_evidence = [
        "docs/product/local-install-verification-2026-06-28.md",
        "docs/product/docker-install-verification-2026-06-28.md",
        "docs/product/hosted-api-quickstart-verification-2026-06-28.md",
        "docs/product/skill-usage-verification-2026-06-29.md",
        "docs/product/website-route-render-verification-2026-06-29.md",
        "docs/product/website-copy-review-2026-06-28.md",
        "docs/product/feature-list.md",
        "docs/product/differentiation.md",
        "docs/legal/legal-readiness-checklist.md",
        "docs/legal/dependency-license-inventory-2026-06-28.md",
        "docs/product/private-beta-onboarding-and-support.md",
    ]
    for evidence_file in current_evidence:
        assert evidence_file in launch_plan

    public_preview_blockers = [
        "Publish package to PyPI",
        "Publish Docker image to GHCR or Docker Hub",
        "Run GitHub Release workflow against real `v*` tag",
        "Smoke downloaded GitHub Release artifacts",
        "Certify public hosted checkout",
        "Replace beta legal placeholders",
        "Claim clean dependency security posture",
    ]
    for blocker in public_preview_blockers:
        assert blocker in launch_plan

    prohibited_claims = [
        "PyPI availability",
        "GHCR or Docker Hub image availability",
        "Public self-serve hosted signup",
        "Unlimited hosted crawling",
        "Certified legacy `/app` UI",
        "Guaranteed hard-site bypass",
        "Security-clean dependency audit",
    ]
    for claim in prohibited_claims:
        assert claim in launch_plan

    stale_open_items = [
        "- [ ] Fix current Ruff failure in `tests/e2e_real_websites.py`.",
        "- [ ] Add feature list, differentiation, legal readiness, and third-party notices.",
        "- [ ] Add a private-beta website page.",
        "- [ ] Publish polished README.",
        "- [ ] Add installation and Docker guide.",
        "- [ ] Add API examples.",
        "- [ ] Add dependency/license inventory.",
    ]
    for stale_item in stale_open_items:
        assert stale_item not in launch_plan


def test_release_checklist_blocks_public_launch_until_decisions_are_closed() -> None:
    checklist = _read("docs/product/release-checklist.md")

    required_gates = [
        "License decision recorded",
        "GitHub release artifact workflow",
        "Clean wheel install smoke",
        "Docker runtime smoke",
        "Hosted economics and usage limits",
        "Security policy",
        "Private beta feedback templates",
        "Third-party notices",
        "No public registry publish",
    ]
    for gate in required_gates:
        assert gate in checklist

    assert "Public launch is blocked until" in checklist
    assert "PyPI" in checklist
    assert "GHCR" in checklist
    assert "Docker Hub" in checklist
    assert "docs/product/launch-decision-request-2026-06-29.md" in checklist


def test_hosted_economics_and_usage_limits_are_documented_without_approval() -> None:
    economics = _read("docs/product/hosted-economics-and-usage-limits.md")
    checklist = _read("docs/product/release-checklist.md")
    pricing_refresh = _read(
        "docs/competetor-website-knowledge/market-pricing-refresh-2026-06-29.md"
    )
    source_index = _read("docs/competetor-website-knowledge/source-index.md")

    assert "Hosted Economics And Usage Limits" in economics
    assert "$22 one-time hosted beta pass" in economics
    assert "finite hosted credits" in economics
    assert "No unlimited hosted crawling" in economics
    assert "Standard credits | 2,000" in economics
    assert "Browser credits | 100" in economics
    assert "Browser render | browser | 5" in economics
    assert "Browser minute | browser | 10" in economics
    assert "Firecrawl" in economics
    assert "Browserbase" in economics
    assert "market-pricing-refresh-2026-06-29.md" in economics
    assert "mature crawler, browser, search, and extraction products meter" in economics
    assert "Subscriptions can follow after private-beta usage data is measured" in economics
    assert "- [ ] Public launch pricing and hosted usage limits approved." in checklist
    assert (
        "- [x] Hosted economics and usage limits documented against the `$22` beta pass"
        in checklist
    )
    assert "docs/product/hosted-economics-and-usage-limits.md" in checklist
    assert "Market Pricing Refresh" in pricing_refresh
    assert "Local Scout should stay free" in pricing_refresh
    assert "Browserbase" in pricing_refresh
    assert "ScrapingBee" in pricing_refresh
    assert "Zyte" in pricing_refresh
    assert "Do not approve public pricing yet." in pricing_refresh
    assert "Approve $22 as a private-beta finite-credit pass." in pricing_refresh
    assert "Do not approve $22 as a public, unlimited, or lifetime hosted plan." in (
        pricing_refresh
    )
    assert "market-pricing-refresh-2026-06-29.md" in source_index


def test_website_copy_review_records_competitor_alignment_and_boundaries() -> None:
    review = _read("docs/product/website-copy-review-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")
    website_plan = _read("docs/competetor-website-knowledge/scout-website-plan.md")

    assert "Website Copy Review Against Competitor Research" in review
    assert "competitor-matrix.md" in review
    assert "website-patterns.md" in review
    assert "Firecrawl" in review
    assert "local-first acquisition" in review
    assert "source evidence" in review
    assert "blocked-page evidence" in review
    assert "typed records" in review
    assert "unlimited hosted scraping" in review
    assert "Scout the utility /\nservice layer" in website_plan
    assert "The legacy `/app` UI." in website_plan
    assert "not\nlifetime hosted access" in website_plan
    assert "guaranteed hard-site bypass" in review
    assert "Public launch pricing and hosted usage limits approved" in review
    assert "- [x] Website copy reviewed against competitor research." in checklist
    assert "docs/product/website-copy-review-2026-06-28.md" in checklist


def test_website_route_render_verification_records_local_server_smoke() -> None:
    verification = _read("docs/product/website-route-render-verification-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Website Route And Render Verification" in verification
    assert "Launch website route/render smoke passed locally" in verification
    assert "python3 -m pytest tests/unit/website/test_launch_website.py -q" in verification
    assert "10 passed, 2 warnings" in verification
    assert "python3 -m scout.cli serve --host 127.0.0.1 --port 18423" in verification
    assert "`/quickstart`" in verification
    assert "`/pricing`" in verification
    assert "`/beta`" in verification
    assert "`/?checkout=success`" in verification
    assert "`/?checkout=cancelled`" in verification
    assert "`/beta?checkout=success`" in verification
    assert "`/beta?checkout=cancelled`" in verification
    assert "Stripe checkout return status" in verification
    assert "`/third-party-notices`" in verification
    assert "docs/product/screenshots/website-2026-06-29/home.png" in verification
    assert "docs/product/screenshots/website-2026-06-29/quickstart.png" in verification
    assert "docs/product/screenshots/website-2026-06-29/pricing.png" in verification
    assert "docs/product/screenshots/website-2026-06-29/beta.png" in verification
    assert "It does not prove the old `/app` interface is usable." in verification
    assert "- [x] Launch website routes and browser render smoke verified locally." in checklist
    assert "docs/product/website-route-render-verification-2026-06-29.md" in checklist
    assert "This does not certify" in checklist


def test_local_install_verification_records_verified_beta_branch_path() -> None:
    verification = _read("docs/product/local-install-verification-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Local Install Verification" in verification
    assert "Private-beta branch install path verified" in verification
    assert "codex/scout-platform-foundation" in verification
    assert "scout_web-0.1.0-py3-none-any.whl" in verification
    assert "import-ok" in verification
    assert "installed distribution version `0.1.0`" in verification
    assert "scout --help" in verification
    assert "Authenticated scrape check" in verification
    assert "success`: `true" in verification
    assert "PackageNotFoundError" in verification
    assert "older/default-branch package `scout==0.1.0`" in verification
    assert (
        "- [x] Local install instructions tested on a fresh machine or clean container."
        in checklist
    )
    assert "docs/product/local-install-verification-2026-06-28.md" in checklist
    assert "branch-qualified" in checklist


def test_product_export_generalization_verification_records_non_algolia_exports() -> None:
    verification = _read("docs/product/product-export-generalization-verification-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Product Export Generalization Verification" in verification
    assert "Verified for private beta." in verification
    assert "Scout's product workflow is no longer Algolia-only." in verification
    assert "ProductExportFormat.JSON" in verification
    assert "ProductExportFormat.JSONL" in verification
    assert "ProductExportFormat.CSV" in verification
    assert "ProductExportFormat.SQLITE" in verification
    assert "ProductExportFormat.GOOGLE_SHEETS" in verification
    assert "scout product-export" in verification
    assert "24 passed, 8 warnings" in verification
    assert "google_sheets_csv_exists True" in verification
    assert "Direct Google Sheets API push is intentionally not enabled" in verification
    assert "- [x] Product records export beyond Algolia." in checklist
    assert "docs/product/product-export-generalization-verification-2026-06-29.md" in checklist
    assert "Direct Google Sheets API push and webhook export remain future work." in checklist


def test_distribution_package_plan_reflects_verified_beta_paths_and_blocks_registries() -> None:
    distribution = _read("docs/product/distribution-package-plan.md")

    assert (
        "Controlled private beta distribution plan; public registry publishing blocked"
        in distribution
    )
    assert "docs/product/launch-evidence-index-2026-06-29.md" in distribution
    assert "docs/product/registry-publishing-policy-2026-06-29.md" in distribution
    assert "docs/legal/scout-license-distribution-decision-brief-2026-06-29.md" in distribution
    assert "docs/legal/license-implementation-runbook-2026-06-29.md" in distribution
    assert "scout launch-readiness" in distribution
    assert "GitHub CI runs the repository wrapper for this checker" in distribution
    assert "scout launch-readiness --require-public" in distribution
    assert "The beta strategy is local-first." in distribution

    beta_surfaces = [
        "Local Python package from GitHub branch",
        "CLI",
        "HTTP service",
        "Docker from source",
        "Hosted API",
        "Skill docs",
    ]
    for surface in beta_surfaces:
        assert surface in distribution

    evidence_files = [
        "docs/product/local-install-verification-2026-06-28.md",
        "docs/product/docker-install-verification-2026-06-28.md",
        "docs/product/hosted-api-quickstart-verification-2026-06-28.md",
        "docs/product/skill-usage-verification-2026-06-29.md",
        "docs/product/website-route-render-verification-2026-06-29.md",
    ]
    for evidence_file in evidence_files:
        assert evidence_file in distribution

    assert (
        'pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"'
        in distribution
    )
    assert "playwright install chromium" in distribution
    assert "SCOUT_API_KEY=dev-key SCOUT_WORKDIR=/tmp/scout-runs scout serve" in distribution
    assert "docker compose -f docker/docker-compose.yml up --build -d" in distribution
    assert "python3 scripts/release_artifact_smoke.py --dist-dir" in distribution
    assert "python3 scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG" in distribution

    package_facts = [
        "`pyproject.toml` defines package name `scout-web`",
        "installed CLI command remains `scout`",
        "Python requirement is `>=3.11`",
        "Hatch wheel packaging includes `THIRD_PARTY_NOTICES.md`",
        "Docker runtime uses `DB_PATH=/data/scout.db`",
    ]
    for fact in package_facts:
        assert fact in distribution

    open_gates = [
        "license decision",
        "final license expression in `pyproject.toml`",
        "`LICENSE` file",
        "release artifact workflow run against an approved real `v*` tag",
        "downloaded GitHub Release artifact smoke",
        "public registry publishing approval",
    ]
    for gate in open_gates:
        assert gate in distribution

    prohibited_claims = [
        "PyPI availability",
        "GHCR or Docker Hub image availability",
        "Public self-serve hosted signup",
        "Public launch readiness",
        "Security-clean dependency audit",
        "Certified legacy `/app` UI",
        "Unlimited hosted crawling",
    ]
    for claim in prohibited_claims:
        assert claim in distribution

    stale_open_items = [
        "- [ ] Python version requirements.",
        "- [ ] Playwright browser install.",
        "- [ ] `.env.local` setup.",
        "- [ ] `SCOUT_API_KEY`.",
        "- [ ] `SCOUT_WORKDIR`.",
        "- [ ] quick health check.",
        "- [ ] quick scrape example.",
        "- [ ] where artifacts are written.",
        "- [ ] Clean generated local residue.",
        "- [ ] Run dependency CVE scan and record result.",
        "- [ ] Run secret scan and record result.",
    ]
    for stale_item in stale_open_items:
        assert stale_item not in distribution


def test_docker_install_verification_records_docs_only_smoke() -> None:
    verification = _read("docs/product/docker-install-verification-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Docker Install Verification" in verification
    assert (
        "docker compose -p scout-docs-smoke -f docker/docker-compose.yml up --build -d"
        in verification
    )
    assert "Docker version 29.1.3" in verification
    assert "Docker Compose version v5.0.1" in verification
    assert "/health" in verification
    assert "/styles.css" in verification
    assert "/quickstart" in verification
    assert "/docs" in verification
    assert "OpenAPI" in verification
    assert "Authenticated scrape" in verification
    assert "quality score `1.0`" in verification
    assert "data-ok" in verification
    assert "stale local Python/uvicorn Scout server" in verification
    assert "docker compose -p scout-docs-smoke -f docker/docker-compose.yml down -v" in verification
    assert "- [x] Docker install instructions tested from docs only." in checklist
    assert "docs/product/docker-install-verification-2026-06-28.md" in checklist
    assert "stale local uvicorn process" in checklist


def test_hosted_api_quickstart_verification_records_new_key_smoke() -> None:
    verification = _read("docs/product/hosted-api-quickstart-verification-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Hosted API Quickstart Verification" in verification
    assert "freshly generated hosted beta key" in verification
    assert "python3 -m scout.cli hosted-provision" in verification
    assert "/v1/hosted/me" in verification
    assert "/v1/hosted/scrape" in verification
    assert "hosted_beta_pass" in verification
    assert "raw_api_key_masked" in verification
    assert "scrape_success: true" in verification
    assert "credits_charged: 1" in verification
    assert "provider: crawl4ai" in verification
    assert "quality_score: 1.0" in verification
    assert "before_standard: 2000" in verification
    assert "after_standard: 1999" in verification
    assert "- [x] Hosted API quickstart tested with a newly generated API key." in checklist
    assert "docs/product/hosted-api-quickstart-verification-2026-06-28.md" in checklist


def test_hosted_operating_contract_documents_private_beta_boundary() -> None:
    contract = _read("docs/product/hosted-operating-contract-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    evidence = _read("docs/product/launch-evidence-index-2026-06-29.md")

    assert "Hosted Scout Operating Contract" in contract
    assert "Private-beta hosted operating contract" in contract
    assert "Local Scout" in contract
    assert "Hosted Scout" in contract
    assert "scout hosted-provision --email tester@example.com --db hosted.sqlite" in contract
    assert "stores the API key hash, not the raw key" in contract
    assert "Authorization: Bearer scout_live_" in contract
    assert "GET /v1/hosted/me" in contract
    assert "POST /v1/hosted/scrape" in contract
    assert "POST /v1/hosted/crawl" in contract
    assert "POST /v1/hosted/products" in contract
    assert "POST /v1/hosted/run/{use_case}" in contract
    assert "GET /v1/hosted/runs/{run_id}/artifacts" in contract
    assert "`hosted_beta_pass` | 2,000 | 100 | 7 days | 100 | 1" in contract
    assert "browser render | browser | 5" in contract
    assert "browser minute | browser | 10" in contract
    assert "server `SCOUT_WORKDIR`" in contract
    assert "tenant_id" in contract
    assert "another tenant receives `404`" in contract
    assert "distributed/global rate limiting" in contract
    assert "production database such as Postgres" in contract
    assert "object storage with tenant-scoped keys" in contract
    assert "real Stripe test-mode checkout and webhook smoke" in contract
    assert "Production-ready multi-tenant SaaS" in contract
    assert "docs/product/hosted-operating-contract-2026-06-29.md" in checklist
    assert "Hosted operating contract documented for private beta" in checklist
    assert "docs/product/hosted-operating-contract-2026-06-29.md" in evidence
    assert "This does not approve public self-serve hosted Scout." in evidence


def test_scalability_security_audit_separates_private_beta_from_public_hosted_launch() -> None:
    audit = _read("docs/product/scalability-security-audit-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    evidence = _read("docs/product/launch-evidence-index-2026-06-29.md")

    assert "Scout Scalability And Security Launch Audit" in audit
    assert "Private-beta scale/security audit" in audit
    assert "credible for private beta because the user owns compute" in audit
    assert "credible only for controlled private beta with finite" in audit
    assert "blocked until production storage" in audit
    assert "Async queue, worker pools, cancellation, timeouts" in audit
    assert "Object storage with tenant prefixes, signed URLs, retention jobs" in audit
    assert "Redis/distributed rate limit and abuse controls" in audit
    assert "Postgres or managed SQL" in audit
    assert "Crawl4AI/lxml blocker documented" in audit
    assert "real Stripe test-mode checkout and webhook smoke" in audit
    assert "JSONL" in audit
    assert "Google Sheets import CSV" in audit
    assert "direct Google Sheets API push" in audit
    assert "Public hosted API | Blocked" in audit
    assert "Local package private beta | Acceptable with limits" in audit
    assert "Hosted API private beta | Acceptable with limits" in audit
    assert "Load-test hosted run limits against target concurrency" in audit
    assert "docs/product/scalability-security-audit-2026-06-29.md" in checklist
    assert "Scalability and security launch audit documented" in checklist
    assert "docs/product/scalability-security-audit-2026-06-29.md" in evidence
    assert "Public hosted API remains blocked." in evidence


def test_stripe_test_mode_readiness_keeps_live_gate_open_until_real_smoke() -> None:
    readiness = _read("docs/product/stripe-test-mode-readiness-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    distribution = _read("docs/distribution.md")

    assert "Stripe Test-Mode Readiness" in readiness
    assert "Deterministic coverage passed; real Stripe test-mode smoke is still open." in readiness
    assert "22 passed, 2 warnings" in readiness
    assert "STRIPE_SECRET_KEY" in readiness
    assert "STRIPE_BETA_PRICE_ID" in readiness
    assert "STRIPE_WEBHOOK_SECRET" in readiness
    assert "checkout.session.completed" in readiness
    assert "scripts/stripe_test_mode_smoke.py" in readiness
    assert "It does not" in readiness
    assert "complete the card payment" in readiness
    assert "scripts/stripe_test_mode_smoke.py" in distribution
    assert "Complete the test payment in Stripe Checkout" in distribution
    assert "This gate is **not approved for public launch** yet." in readiness
    assert "- [ ] Stripe checkout and webhook tested in Stripe test mode." in checklist
    assert "docs/product/stripe-test-mode-readiness-2026-06-29.md" in checklist
    assert "real Stripe test-mode credentials/webhook secret" in checklist


def test_dependency_audit_refresh_keeps_lxml_gate_open_until_clean() -> None:
    refresh = _read("docs/security/dependency-audit-refresh-2026-06-29.md")
    risk_decision = _read("docs/security/crawl4ai-lxml-risk-decision-2026-06-28.md")
    exception_packet = _read(
        "docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md"
    )
    checklist = _read("docs/product/release-checklist.md")

    assert "Dependency Audit Refresh" in refresh
    assert "Audit still failing; public launch remains blocked." in refresh
    assert "crawl4ai 0.9.0" in refresh
    assert "lxml 5.4.0" in refresh
    assert "`lxml` latest available version: `6.1.1`" in refresh
    assert "PYSEC-2026-87" in refresh
    assert "ResolutionImpossible" in refresh
    assert "continue-on-error: true" in refresh
    assert "Scout is not public-launch-ready while this dependency audit fails." in refresh
    assert "Refresh on 2026-06-29" in risk_decision
    assert "Proposed private-beta exception packet" in risk_decision
    assert "Crawl4AI/lxml Private-Beta Exception Packet" in exception_packet
    assert "not approved" in exception_packet
    assert "hosted usage remains capped and metered" in exception_packet
    assert "docs/security/dependency-audit-refresh-2026-06-29.md" in checklist
    assert "docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md" in checklist
    assert "- [ ] Crawl4AI/lxml risk decision approved." in checklist
    assert "- [ ] Dependency audit clean and blocking in GitHub CI." in checklist


def test_license_distribution_decision_brief_keeps_release_gates_open() -> None:
    brief = _read("docs/legal/scout-license-distribution-decision-brief-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    legal_checklist = _read("docs/legal/legal-readiness-checklist.md")
    runbook = _read("docs/legal/license-implementation-runbook-2026-06-29.md")

    assert "Scout License And Distribution Decision Brief" in brief
    assert "Decision required before public registry publishing." in brief
    assert "Recommended path" in brief
    assert "Apache-2.0 for Scout's local/core package" in brief
    assert "Crawl4AI license" in brief
    assert "https://github.com/unclecode/crawl4ai/blob/main/LICENSE" in brief
    assert "Using Crawl4AI internally is not blocked by a royalty requirement" in brief
    assert "Do not publish to PyPI" in brief
    assert "Do not publish Docker images to Docker Hub or GHCR" in brief
    assert "Decision Needed" in brief
    assert "license-implementation-runbook-2026-06-29.md" in brief
    assert "scripts/license_release_gate_check.py" in brief
    assert "Scout License Implementation Runbook" in runbook
    assert "waiting for license decision" in runbook
    assert "python3 scripts/license_release_gate_check.py" in runbook
    assert "- [ ] Approve Apache-2.0 for Scout local/core." in brief
    assert "- [ ] License decision recorded." in checklist
    assert "- [ ] Final license expression added to `pyproject.toml`." in checklist
    assert "- [ ] `LICENSE` file added if Scout is open source or source-available." in checklist
    assert "scout-license-distribution-decision-brief-2026-06-29.md" in checklist
    assert "scout-license-distribution-decision-brief-2026-06-29.md" in legal_checklist
    assert "license-implementation-runbook-2026-06-29.md" in legal_checklist


def test_registry_publishing_policy_blocks_public_registries_until_approved() -> None:
    policy = _read("docs/product/registry-publishing-policy-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    distribution = _read("docs/product/distribution-package-plan.md")

    assert "Registry Publishing Policy" in policy
    assert "Policy recommended; approval required before registry publishing." in policy
    assert "`v*` tags may create a GitHub Release" in policy
    assert "must **not** publish to PyPI" in policy
    assert "must **not** push Docker images to GHCR or Docker Hub" in policy
    assert "scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG" in policy
    assert "twine upload" in policy
    assert "docker/build-push-action" in policy
    assert "PyPI first if license/security gates close" in policy
    assert "GHCR before Docker Hub" in policy
    assert "Defer Docker Hub until there is user demand" in policy
    assert "- [ ] Registry publishing policy approved" in checklist
    assert "- [ ] Docker image publishing policy approved." in checklist
    assert "docs/product/registry-publishing-policy-2026-06-29.md" in checklist
    assert "docs/product/registry-publishing-policy-2026-06-29.md" in distribution


def test_launch_decision_dashboard_lists_current_open_gates_and_next_decisions() -> None:
    dashboard = _read("docs/product/launch-decision-dashboard-2026-06-29.md")
    request = _read("docs/product/launch-decision-request-2026-06-29.md")

    assert "Scout Launch Decision Dashboard" in dashboard
    assert "docs/product/launch-decision-request-2026-06-29.md" in dashboard
    assert "Private beta can continue with limits; public launch is blocked." in dashboard
    assert "Scout is not ready for public launch." in dashboard
    assert "Open Decisions" in dashboard
    assert "Open Verification Gates" in dashboard
    assert "Evidence Already Closed" in dashboard
    assert "Recommended Next Order" in dashboard
    assert "Approve Apache-2.0 for Scout local/core" in dashboard
    assert "Crawl4AI/lxml blocker" in dashboard
    assert "Stripe test-mode credentials" in dashboard
    assert "scripts/stripe_test_mode_smoke.py --create-checkout" in dashboard
    assert "scripts/release_artifact_smoke.py --dist-dir" in dashboard
    assert "scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG" in dashboard
    assert "Approve one artifact-only private beta tag" in dashboard
    assert "Do not publish `scout-web` to PyPI." in dashboard
    assert "Do not push Docker images to GHCR or Docker Hub." in dashboard
    assert "Scout Launch Decision Request" in request
    assert "Approve Scout for **controlled private beta only**." in request
    assert "License: Apache-2.0 approved for Scout local/core." in request
    assert "Crawl4AI/lxml: limited private-beta exception approved" in request
    assert "Hosted beta: keep $22 finite-credit one-time beta pass." in request
    assert "Release tag: approve one artifact-only private-beta v* tag" in request
    assert "Docker registry: defer GHCR/Docker Hub." in request
    assert "What Not To Approve Yet" in request


def test_launch_gate_burndown_classifies_open_work_by_owner_and_blocker() -> None:
    burndown = _read("docs/product/launch-gate-burndown-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Scout Launch Gate Burndown" in burndown
    assert "docs/product/launch-decision-request-2026-06-29.md" in burndown
    assert "Private beta can continue; public launch remains blocked" in burndown
    assert "Gate Burndown" in burndown
    assert "Blocker type" in burndown
    assert "Owner" in burndown
    assert "Codex-Executable Work Remaining" in burndown
    assert "License decision" in burndown
    assert "Arijit decision" in burndown
    assert "Final license expression" in burndown
    assert "scripts/license_release_gate_check.py" in burndown
    assert "GitHub release workflow on real `v*` tag" in burndown
    assert "scripts/release_artifact_smoke.py --dist-dir" in burndown
    assert "Stripe real test-mode smoke" in burndown
    assert "scripts/stripe_test_mode_smoke.py --create-checkout" in burndown
    assert "External credentials/webhook" in burndown
    assert "Crawl4AI/lxml risk decision" in burndown
    assert "crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md" in burndown
    assert "Dependency audit clean and blocking in CI" in burndown
    assert "scripts/docker_image_smoke.py ghcr.io/OWNER/IMAGE:TAG" in burndown
    assert "website-route-render-verification-2026-06-29.md" in burndown
    assert "Do Not Claim Yet" in burndown
    assert "certified app UI" in burndown
    assert "hard-site bypass guarantees" in burndown
    assert "Current launch gate burndown" in checklist
    assert "docs/product/launch-gate-burndown-2026-06-29.md" in checklist
    assert "docs/product/launch-decision-dashboard-2026-06-29.md" in checklist


def test_public_launch_action_packet_groups_executable_blocker_types() -> None:
    action_packet = _read("docs/product/public-launch-action-packet-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    dashboard = _read("docs/product/launch-decision-dashboard-2026-06-29.md")
    burndown = _read("docs/product/launch-gate-burndown-2026-06-29.md")

    assert "Scout Public Launch Action Packet" in action_packet
    assert "Generated from `scout launch-readiness --json`" in action_packet
    assert "Private beta remains `ready_with_limits`." in action_packet
    assert "Public launch remains `blocked`." in action_packet
    assert "`founder_decision`" in action_packet
    assert "`legal_implementation`" in action_packet
    assert "`engineering`" in action_packet
    assert "`risk_decision`" in action_packet
    assert "`external_smoke`" in action_packet
    assert "Approve Apache-2.0 for Scout local/core" in action_packet
    assert "Keep $22 as a finite-credit hosted beta pass" in action_packet
    assert "Do not approve public self-serve hosted launch yet" in action_packet
    assert "GitHub release workflow run" in action_packet
    assert "Stripe real test-mode smoke" in action_packet
    assert "Crawl4AI/lxml risk decision" in action_packet
    assert "scout launch-decision-draft" in action_packet
    assert "python3 scripts/founder_decision_record_draft.py" in action_packet
    assert "--blocker-id license-decision" in action_packet
    assert "docs/product/public-launch-action-packet-2026-06-29.md" in checklist
    assert "docs/product/public-launch-action-packet-2026-06-29.md" in dashboard
    assert "docs/product/public-launch-action-packet-2026-06-29.md" in burndown
    assert "docs/product/public-launch-action-packet-2026-06-29.md" in _read(
        "docs/product/launch-evidence-index-2026-06-29.md"
    )


def test_founder_decision_record_template_captures_launch_gate_approvals() -> None:
    template = _read("docs/product/founder-decision-record-template-2026-06-29.md")
    action_packet = _read("docs/product/public-launch-action-packet-2026-06-29.md")
    request = _read("docs/product/launch-decision-request-2026-06-29.md")

    assert "Scout Founder Decision Record Template" in template
    assert "Decision ID" in template
    assert "Decision owner" in template
    assert "Approved decision" in template
    assert "Rejected alternatives" in template
    assert "Scope and limits" in template
    assert "Required Codex follow-up" in template
    assert "Expiration or revisit trigger" in template
    assert "License decision" in template
    assert "Crawl4AI/lxml risk decision" in template
    assert "Hosted beta pricing" in template
    assert "Artifact-only private beta tag" in template
    assert "Docker image publishing policy" in template
    assert "Stripe real test-mode smoke" in template
    assert "founder-decision-drafts" in template
    assert "scout launch-decision-draft" in template
    assert "scout launch-decision-check" in template
    assert "python3 scripts/founder_decision_record_draft.py" in template
    assert "python3 scripts/founder_decision_record_check.py" in template
    assert "scout launch-decision-check" in action_packet
    assert "python3 scripts/founder_decision_record_check.py" in action_packet
    assert "Do not use this template to approve public launch by accident." in template
    assert "docs/product/founder-decision-record-template-2026-06-29.md" in action_packet
    assert "docs/product/founder-decision-record-template-2026-06-29.md" in request


def test_launch_evidence_index_maps_claims_to_proof_and_preserves_blockers() -> None:
    evidence = _read("docs/product/launch-evidence-index-2026-06-29.md")
    checklist = _read("docs/product/release-checklist.md")
    dashboard = _read("docs/product/launch-decision-dashboard-2026-06-29.md")
    burndown = _read("docs/product/launch-gate-burndown-2026-06-29.md")

    assert "Scout Launch Evidence Index" in evidence
    assert "What is actually verified, what is blocked, and where is the proof?" in evidence
    assert "Scout is credible for controlled private beta with limits." in evidence
    assert "Scout is not public-launch-ready." in evidence
    assert "If a claim is not listed here with a proof file, treat it as unverified." in evidence
    assert "Do not claim" in evidence
    assert "certified legacy `/app` UI" in evidence
    assert "unlimited hosted crawling" in evidence
    assert "guaranteed hard-site bypass" in evidence

    required_proof_files = [
        "docs/product/website-route-render-verification-2026-06-29.md",
        "docs/product/website-copy-review-2026-06-28.md",
        "docs/competetor-website-knowledge/",
        "docs/product/local-install-verification-2026-06-28.md",
        "docs/product/docker-install-verification-2026-06-28.md",
        "docs/product/hosted-api-quickstart-verification-2026-06-28.md",
        "docs/product/skill-usage-verification-2026-06-29.md",
        "docs/product/product-export-generalization-verification-2026-06-29.md",
        "docs/product/hosted-economics-and-usage-limits.md",
        "docs/product/stripe-test-mode-readiness-2026-06-29.md",
        "scripts/stripe_test_mode_smoke.py",
        "scripts/release_artifact_smoke.py",
        "scripts/docker_image_smoke.py",
        "docs/legal/scout-license-distribution-decision-brief-2026-06-29.md",
        "docs/legal/license-implementation-runbook-2026-06-29.md",
        "scripts/license_release_gate_check.py",
        "docs/security/dependency-audit-refresh-2026-06-29.md",
        "docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md",
        "docs/product/private-beta-onboarding-and-support.md",
        ".github/ISSUE_TEMPLATE/private_beta_bug.yml",
        ".github/ISSUE_TEMPLATE/private_beta_feature.yml",
    ]
    for proof_file in required_proof_files:
        assert proof_file in evidence

    required_boundaries = [
        "Does not certify the legacy `/app` UI.",
        "This is a branch/private-beta install path, not PyPI.",
        "Image publishing to GHCR/Docker Hub is not approved.",
        "Hosted beta remains approved-testers-only.",
        "Real Stripe test-mode payment and webhook are still open.",
        "No approved release tag has been run yet.",
        "No published image is approved yet.",
        "No license decision is approved",
        "Public launch remains blocked until the audit is clean",
    ]
    for boundary in required_boundaries:
        assert boundary in evidence

    open_gates = [
        "Scout license",
        "Final license expression",
        "`LICENSE` file",
        "Public pricing and hosted usage limits",
        "Registry publishing policy",
        "Crawl4AI/lxml risk",
        "Stripe real test-mode smoke",
        "Final hosted terms/privacy",
    ]
    for gate in open_gates:
        assert gate in evidence

    assert "docs/product/launch-evidence-index-2026-06-29.md" in checklist
    assert "docs/product/launch-evidence-index-2026-06-29.md" in dashboard
    assert "docs/product/launch-evidence-index-2026-06-29.md" in burndown
    assert "scout launch-readiness" in checklist
    assert (
        "GitHub CI runs the repository wrapper, `python3 scripts/launch_readiness_check.py`"
        in evidence
    )
    assert "GitHub CI runs the repository wrapper default and JSON forms" in checklist
    assert "scout launch-readiness --require-public" in evidence
