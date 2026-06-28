# Hosted Account Service SOP Constraints

## Source

The module-builder skill points to Google Drive SOP files that are not part of
this repository checkout. Current implementation follows the active AGENTS and
developer instructions instead.

## Coding Constraints Applied

- Use Pydantic models at module boundaries.
- Keep raw secrets out of stored models.
- Keep functions focused and typed.
- Prefer dependency injection through a store class instead of global state.
- Avoid public HTTP endpoints until the domain contract is tested.

## Testing Constraints Applied

- TDD: write tests before implementation.
- Unit tests first because this is pure domain logic with no I/O.
- Assert behavior, not implementation details.
- Include mutation safety tests for insufficient-credit paths.
