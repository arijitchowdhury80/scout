# Scout Beta Privacy Placeholder

Date: 2026-06-28
Status: Placeholder for private beta only

This is not a final Privacy Policy. It records the current beta data-handling
posture until lawyer-reviewed privacy terms are approved.

## Local Scout

Local Scout keeps run artifacts on the user's machine in the configured working
directory. Local artifacts can include records, source pages, blocked pages,
screenshots or DOM evidence when captured, validation files, logs, and reports.

Delete local run folders when the evidence is no longer needed.

## Hosted Beta

Hosted beta may store account email, payment references, API key status, run
metadata, source URLs, extracted records, blocked evidence, logs, and artifacts
long enough to operate, debug, meter, and support the beta.

Hosted retention and deletion policy still needs final approval before broad
hosted launch.

## Sensitive Data And Credentials

- Do not submit secrets or regulated personal data.
- API keys should stay in `.env.local` for local development or in deployment
  secret managers for hosted deployments.
- Keys must not be committed, pasted into public prompts, or stored in run
  artifacts.
- Browser-assisted acquisition may capture screenshots, DOM, markdown, links,
  network diagnostics, console errors, and source hashes. These artifacts can
  contain visible page data, so avoid private sessions unless you have explicit
  permission.

