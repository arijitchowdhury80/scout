# Hosted Payment Provisioning SOP Constraints

Read:

- Coding SOPs from ArijitOS Brain Standards.
- Testing SOPs from ArijitOS Brain Standards.
- Project `AGENTS.md`.

Applicable constraints:

- Pydantic models on every boundary request/result/record.
- Test first; scenario list before tests.
- Dependency injection for persistence and account service.
- No raw dicts crossing module boundaries.
- Typed functions and pyright-clean implementation.
- No raw API key persistence; verify by reading SQLite bytes/text.
- Keep functions small and single-purpose where practical.
- Use structured domain result objects instead of broad exceptions for expected
  checkout rejection paths.

Known practical adaptation:

- This slice uses unit tests with a real temporary SQLite file. That gives the
  required persistence behavior without external services.

