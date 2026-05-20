# Scout Frontend

Scout's standalone HTTP app includes a self-educating frontend at `/app`.

## Product Direction

The frontend is an operator console for Scout's multi-use-case intelligence
engine. It is not a marketing page and not a thin Swagger replacement.

The first production UI includes:

- How to use me
- Run Console
- Product Workbench
- Algolia Preparation
- Run Monitor
- Evidence Browser
- Records Explorer
- Settings

## Architecture Home

The How to use me screen is the first polished frontend slice. It mirrors the
Generated Image 1 architecture concept and teaches Scout as a flow:

```text
Front Doors -> RunRequest -> Execution Mode Router -> Provider Modes
-> Normalized Source Evidence -> Vertical Processors -> Typed Records
-> Downstream Consumers
```

Each stage is clickable and updates a detail panel with what the stage does,
when to use it, and a concrete command or artifact example. The cross-cutting
rail covers security, throttling, observability, retry policy, metrics, storage,
and configuration.

## Working Directory UX

The frontend uses a hybrid working-directory model:

- supported browsers can use a folder picker for local selection,
- unsupported browsers use a manual server-local path,
- the resolved output directory is shown before a run starts.

The browser cannot freely browse the server filesystem in every environment, so
manual path entry remains the reliable fallback.

## Product Workbench

The Product Workbench is designed for ecommerce workflows such as:

```text
Use Scout to get top skincare products from esteelauder.com and prepare
Algolia-ready records.
```

It supports product crawl inputs, record preview, JSON preview, completeness
signals, blocked-page status, and Algolia preparation hooks.

Real Algolia ingestion is intentionally deferred. Production V1 includes a
preview/stub endpoint that validates required fields and credential presence
without writing records to Algolia.

## Secret Handling

Algolia App ID and API key values entered in the UI are session-only request
inputs. Scout validates whether they are present, but never echoes the API key
in responses and must not write it to artifacts, logs, `.env.local`, or browser
storage.

## Design Concept

The generated concept board covers three screens:

1. Scout Command Center
2. Scout Product Workbench
3. Scout Evidence Browser

Generated concept images:

- `docs/design/scout-command-center-concept.png`
- `docs/design/scout-product-workbench-concept.png`
- `docs/design/scout-evidence-browser-concept.png`

Visual direction: light enterprise operator console, dense but readable panels,
execution-mode tabs, restrained teal/indigo accents, 8px radius, and strong
record/evidence inspection affordances.
