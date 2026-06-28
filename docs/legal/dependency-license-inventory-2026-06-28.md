# Scout Dependency License Inventory

Date: 2026-06-28
Status: Metadata-derived runtime inventory for launch review

Generated from a clean runtime install of Scout using `pip install .`.
This is a metadata-derived inventory, not legal advice.
Missing license metadata requires manual review against upstream sources before public launch.

## Known Security/Launch Note

The dependency audit still reports `PYSEC-2026-87` for `lxml 5.4.0` via the Crawl4AI/lxml dependency path. Public launch remains blocked until that risk is resolved or formally excepted.

## Inventory

| Package | Version | Scope | License metadata | Source/Homepage | Notes |
|---|---:|---|---|---|---|
| aiosqlite | 0.22.1 | direct | OSI Approved :: MIT License | Documentation, https://aiosqlite.omnilib.dev; Github, https://github.com/omnilib/aiosqlite |  |
| algoliasearch | 4.44.1 | direct | OSI Approved :: MIT License | Homepage, https://www.algolia.com; Repository, https://github.com/algolia/algoliasearch-client-python |  |
| anyio | 4.14.1 | selected transitive | missing | Documentation, https://anyio.readthedocs.io/en/latest/; Changelog, https://anyio.readthedocs.io/en/stable/versionhistory.html | Missing license metadata requires manual review. |
| Crawl4AI | 0.9.0 | direct | missing | https://github.com/unclecode/crawl4ai | Missing license metadata requires manual review. |
| email-validator | 2.3.0 | direct | OSI Approved :: The Unlicense (Unlicense) | https://github.com/JoshData/python-email-validator |  |
| fastapi | 0.138.1 | direct | missing | Homepage, https://github.com/fastapi/fastapi; Documentation, https://fastapi.tiangolo.com/ | Missing license metadata requires manual review. |
| httpx | 0.28.1 | selected transitive | OSI Approved :: BSD License | Changelog, https://github.com/encode/httpx/blob/master/CHANGELOG.md; Documentation, https://www.python-httpx.org |  |
| lxml | 5.4.0 | selected transitive | OSI Approved :: BSD License | https://lxml.de/ | Also tracked in security audit because of PYSEC-2026-87 via Crawl4AI/lxml. |
| playwright | 1.60.0 | selected transitive | missing | homepage, https://github.com/Microsoft/playwright-python; Release notes, https://github.com/microsoft/playwright-python/releases | Missing license metadata requires manual review. |
| pydantic | 2.13.4 | direct | missing | Homepage, https://github.com/pydantic/pydantic; Documentation, https://docs.pydantic.dev | Missing license metadata requires manual review. |
| pydantic-settings | 2.14.2 | direct | OSI Approved :: MIT License | Homepage, https://github.com/pydantic/pydantic-settings; Funding, https://github.com/sponsors/samuelcolvin |  |
| PyYAML | 6.0.3 | direct | OSI Approved :: MIT License | https://pyyaml.org/ |  |
| starlette | 1.3.1 | selected transitive | missing | Homepage, https://github.com/Kludex/starlette; Documentation, https://starlette.dev/ | Missing license metadata requires manual review. |
| structlog | 26.1.0 | direct | OSI Approved :: Apache Software License; OSI Approved :: MIT License | Documentation, https://www.structlog.org/; Changelog, https://github.com/hynek/structlog/blob/main/CHANGELOG.md |  |
| tiktoken | 0.13.0 | direct | MIT License Copyright (c) 2022 OpenAI, Shantanu Jain Permission is hereby granted, free... | homepage, https://github.com/openai/tiktoken; repository, https://github.com/openai/tiktoken |  |
| typer | 0.25.1 | direct | missing | Homepage, https://github.com/fastapi/typer; Documentation, https://typer.tiangolo.com | Missing license metadata requires manual review. |
| typing_extensions | 4.15.0 | selected transitive | missing | Bug Tracker, https://github.com/python/typing_extensions/issues; Changes, https://github.com/python/typing_extensions/blob/main/CHANGELOG.md | Missing license metadata requires manual review. |
| uvicorn | 0.49.0 | direct | missing | Changelog, https://uvicorn.dev/release-notes; Funding, https://github.com/sponsors/encode | Missing license metadata requires manual review. |

## Review Notes

- `direct` means the package is listed in `pyproject.toml` runtime dependencies.
- `selected transitive` means the package is operationally significant for Scout launch review, but this is not a full SBOM.
- This file does not replace legal review, a generated SBOM, or a final release-license decision.
