# ADR: Standalone Scout Package Plus Thin Skill Wrapper

**Date:** 2026-05-13
**Status:** Accepted

## Context

Scout was originally packaged inside an agent skill directory, which blurred
the boundary between product runtime and agent instructions. The user needs
Scout to work independently from terminal, Docker, HTTP, and Python, while
continuing to work as a Claude/Codex skill.

## Decision

Scout is a standalone Python package and service. The Claude/Codex skill is a
thin integration wrapper that calls the standalone package or local HTTP server.

## Rationale

Standalone packaging makes `pip install`, Docker distribution, tests, docs,
examples, and PyPI publication straightforward. Keeping the skill thin prevents
agent-specific instructions from becoming the source of truth for the scraper.

## Consequences

- `scout products` runs directly from terminal without starting the HTTP server.
- `scout serve` remains available for agents and integrations.
- Durable crawl output is written to explicit run folders, not hidden `/tmp`
  locations.
- The skill documentation must point to Scout as an external package/service.
