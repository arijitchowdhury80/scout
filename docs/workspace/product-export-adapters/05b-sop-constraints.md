# Product Export Adapters - SOP Constraints

Date: 2026-06-28

## Coding Rules

- Use Pydantic models at module boundaries.
- Keep adapter functions small and typed.
- No raw print diagnostics.
- No silent failures; let file/SQLite errors raise with context.
- Keep Algolia-specific names out of the generic export layer.
- Use standard library modules for local exports: `json`, `csv`, `sqlite3`.

## Testing Rules

- Scenario list must be written before test code.
- Tests must be written before implementation.
- Unit tests cover pure export behavior with temp directories.
- Contract tests validate Pydantic request/result models.
- No live Google Sheets/API calls in this slice.

## Conflict Notes

The SOP asks for all three layers on every module. For this local adapter slice,
unit and contract tests are required now. Live integration is deferred because
V1 intentionally avoids external services.

