# Scout Frontend Boundary

Scout no longer ships the experimental `/app` UI as a supported product
surface.

## Current Product Surfaces

- Public launch website: `/`, `/quickstart`, `/guide`, `/examples`,
  `/pricing`, `/status`, `/beta`, `/legal`, `/terms`, and `/privacy`.
- Local HTTP API and Swagger docs.
- Hosted beta API under `/v1/hosted/*`.
- CLI.
- Docker-from-source.
- Claude/Codex skill wrapper.

## Removed Surface

The previous static `/app` operator console was removed because it looked like a
product app but did not consistently deliver a full end-to-end workflow. Keeping
it visible created confusion and diluted the stronger product story: Scout is an
evidence-preserving acquisition utility/service.

## Future UI Rule

Any future UI must be designed and certified as a real product surface before it
is exposed. It should not be added back as a static mock or partial dashboard.

If Scout later needs a visual workbench, it should be scoped as a separate
product feature with:

- working navigation,
- live run status,
- persisted run history,
- browser/session capture that is truthful about what it can and cannot do,
- full E2E browser tests,
- no exposed local API key,
- and a documented launch gate.
