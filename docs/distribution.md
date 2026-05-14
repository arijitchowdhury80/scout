# Distribution

Scout is distributed as a standalone Python package and can also be installed
as a Claude/Codex skill integration.

## Standalone Package

```bash
pip install git+https://github.com/arijitchowdhury80/scout.git
playwright install chromium
```

## Development Install

```bash
git clone https://github.com/arijitchowdhury80/scout.git
cd scout
pip install -e ".[dev]"
playwright install chromium
```

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Skill Install

```bash
bash install-skill.sh
```

The skill wrapper should remain thin: it teaches the agent how to call Scout,
but the scraper, crawler, product pipeline, tests, and docs live in the
standalone package.
