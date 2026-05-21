# Data, Integrations, Settings, And Help Workflow

## User Intent

Inspect artifacts, prepare integrations, configure local defaults, and learn how
Scout works without leaving the app.

## Required Inputs

- Data: run output directory or selected run.
- Integrations: Algolia App ID, API key, index name, selected records.
- Settings: default workdir, environment status, live-test flag.
- Help: no inputs.

## Run States

These screens do not start crawls directly. They support the shared run
workspace by showing data, credentials status, configuration, and guidance.

## Result Tabs

Data uses artifact tables and JSON viewers. Integrations uses readiness panels.
Settings uses configuration cards. Help uses architecture and workflow guidance.

## Right Drawer

Artifact drawer shows file path, type, size, preview, and related run. Algolia
drawer shows readiness details without exposing secrets.

## Empty, Error, And Blocked States

No run selected, missing artifact files, invalid Algolia fields, and unavailable
environment values must be explicit visible states.

## Expected Artifacts

No new artifacts unless exporting a preview. Algolia API keys remain session-only
and must not be written to artifacts, logs, local storage, or repo files.

## Controls

Artifact open/download/copy path, Algolia preview, clear credentials, settings
refresh, docs links, architecture stage links, and help navigation.
