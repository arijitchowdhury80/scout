# Scout Skill Wrapper

This directory contains the Claude/Codex skill wrapper for Scout.

For beta testers, the skill should call hosted HTTP:

```bash
export SCOUT_HOSTED_BASE_URL="https://scout.chowmes.com"
export SCOUT_HOSTED_API_KEY="paste-your-generated-key"
```

Operator-only local verification can install the package from the verified
branch:

```bash
pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-saas-prod-ready"
python -m playwright install chromium
scout serve
curl http://localhost:8421/health
```

Install the skill wrapper:

```bash
bash install-skill.sh
```

The skill teaches the agent how to call Scout for:

- web page scraping
- sitemap and URL discovery
- multi-page crawls
- structured extraction
- screenshots
- product catalog crawling
- Algolia-ready product artifacts
- hosted API quickstart guidance

During private beta, hosted HTTP plus this skill are the tester distribution
paths. The registry command `pip install scout-web` is reserved for after the
license and publishing gates close.

The runtime, tests, internal Docker files, and product documentation live in the
Scout repository: <https://github.com/arijitchowdhury80/scout>.
