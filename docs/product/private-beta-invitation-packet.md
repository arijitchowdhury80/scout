# Private Beta Invitation Packet

Date: 2026-06-29

Status: operator recruiting packet for controlled private beta

Use this packet before inviting testers. The goal is to recruit 5-10 trusted
testers who can validate Scout's local-first acquisition workflow, artifact
model, hosted finite-credit path, and feedback loop without mistaking private
beta for public launch.

## Who To Invite

Start with 5-10 trusted testers across these profiles:

- solutions engineers who build search demos or product catalogs,
- AI-agent builders who need local acquisition tools,
- competitive intelligence researchers,
- RevOps or data teams that need website-to-record workflows,
- technical users willing to inspect artifacts and file precise feedback.

Good testers are comfortable with a CLI, HTTP API, Docker, or agent-backed
workflow. They do not need a polished app UI.

## Do Not Invite

Do not invite users who need:

- unlimited hosted crawling,
- guaranteed hard-site bypass,
- production hosted uptime or SLA,
- legal approval for restricted websites,
- a polished no-code app experience,
- public registry packages only,
- production procurement, SOC2, or enterprise support.

These are not Scout private-beta promises.

## Preflight checklist

Before sending invitations:

```bash
scout launch-readiness
scout launch-decision-check --check-existing --check-drafts
python3 -m pytest tests/unit/ -q
```

Confirm:

- private beta reports `ready_with_limits`,
- public launch remains `blocked`,
- founder decision drafts are still deferred review aids,
- the tester handoff exists at `docs/product/private-beta-tester-handoff.md`,
- hosted beta keys are provisioned only for approved testers,
- no public issue asks testers to paste secrets.

## Invite email

Subject: Scout private beta invite: local-first web acquisition

Hi [name],

I am opening a small Scout private beta for technical testers.

Scout is a local-first web acquisition utility. It helps turn public web pages
or captured browser evidence into records, source pages, blocked-page evidence,
and portable artifacts. It is not a promise to bypass every hard site.

The beta is best if you can spend 30 minutes on one target and tell me:

- whether setup worked,
- whether you found the run artifacts,
- whether the records and source evidence were useful,
- where the workflow was confusing or failed.

Start here:

`docs/product/private-beta-tester-handoff.md`

Important boundaries:

- local install is the primary path,
- hosted beta is finite-credit and approved-testers-only,
- no unlimited hosted crawling,
- no guaranteed hard-site bypass,
- do not paste API keys, cookies, secrets, or private customer data into issues.

If you are interested, reply with your preferred path: local package, Docker,
hosted API, or skill/agent usage.

Thanks,
Arijit

## Follow-up email

Subject: Scout beta follow-up: one run and one feedback item

Hi [name],

Thank you for testing Scout. Could you send one short update with:

- surface used: local package, Docker, hosted API, or skill,
- command or endpoint used,
- target type,
- record count, source count, citation count, and blocked count if available,
- whether you found `records.json` and `source_pages.json`,
- one thing that worked,
- one thing that blocked or confused you.

Please use the private beta issue templates for detailed feedback:

- `.github/ISSUE_TEMPLATE/private_beta_bug.yml`
- `.github/ISSUE_TEMPLATE/private_beta_feature.yml`

Please do not include API keys, cookies, screenshots with secrets, or private
customer data.

## Success metrics

Track these manually during the first private beta cohort:

| Metric | Target |
|---|---:|
| Invite-to-activation | 60% of invited testers complete one run |
| Activation | Tester completes one scrape, company run, product run, or hosted scrape |
| Artifact found | Tester can locate `records.json` and `source_pages.json` |
| Feedback filed | Tester files at least one useful bug, feature request, or reply |
| Value clarity | Tester can explain Scout's value in one sentence |
| Boundary clarity | Tester understands no unlimited hosted crawling and no guaranteed hard-site bypass |

## Cohort Tracker

Use a private tracker, not a public repo file, for names and emails.

Recommended columns:

- tester name,
- email,
- profile,
- invite date,
- selected path,
- hosted key issued yes/no,
- first run complete yes/no,
- artifact found yes/no,
- feedback filed yes/no,
- top blocker,
- next follow-up date.

Do not commit tester names, emails, API keys, target customer data, or private
feedback into the public repository.
