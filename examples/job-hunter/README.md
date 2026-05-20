# Job Hunter Example

This example shows the first Job Hunter workflow shape: describe the roles you
want, salary range, locations, skills, excluded terms, and any companies Scout
should start from.

```bash
scout run jobs \
  --profile examples/job-hunter/job-profile.yaml \
  --output-dir ./scout-runs/job-hunter-demo
```

V1 writes target company records and the standard Scout artifact set:

```text
scout-runs/job-hunter-demo/
  manifest.json
  records.json
  records.jsonl
  source_pages.json
  blocked_pages.json
  validation.json
  extraction_report.md
```

The next Job Hunter build slices will add live company discovery, careers page
detection, ATS extraction, job post matching, and daily scheduled monitoring.

Seeded job URLs can be passed directly:

```bash
scout run jobs \
  --profile examples/job-hunter/job-profile.yaml \
  --job-url https://job-boards.greenhouse.io/eve/jobs/4245857009 \
  --output-dir ./scout-runs/job-hunter-url-demo
```

For a Director-level customer success scoring demo with saved evidence:

```bash
scout run jobs \
  --profile examples/job-hunter/director-cs-profile.yaml \
  --job-url fixture://tests/fixtures/jobs/greenhouse_eve_director_cs.html \
  --output-dir ./scout-runs/job-hunter-fixture-demo
```

Keep personal candidate profiles, compensation targets, and resume-derived match
rules in a private local file or vault-backed config rather than committing them
to the public repository.
