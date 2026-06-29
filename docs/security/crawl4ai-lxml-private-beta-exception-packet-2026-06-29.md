# Crawl4AI/lxml Private-Beta Exception Packet

Date: 2026-06-29
Status: Proposed exception packet; not approved

## Decision Needed

Approve or reject a **limited private-beta-only security exception** for
Scout's current Crawl4AI dependency path resolving vulnerable `lxml 5.4.0`
reported as `PYSEC-2026-87`.

This packet does not approve public launch.

## Scope

In scope if approved:

- controlled private beta,
- branch-qualified local install,
- Docker built from source,
- hosted API access for approved testers only,
- documented beta limits,
- visible dependency-audit failure in CI.

Out of scope even if approved:

- public launch,
- PyPI publish,
- GHCR or Docker Hub publish,
- unlimited hosted crawling,
- security-clean marketing claims,
- broad self-serve hosted signup,
- certified legacy `/app` UI claims.

## Current Evidence

| Evidence | Current finding |
|---|---|
| Dependency audit refresh | `docs/security/dependency-audit-refresh-2026-06-29.md` |
| Latest checked Crawl4AI | `0.9.0` |
| Latest checked lxml | `6.1.1` |
| Scout resolved lxml | `5.4.0` |
| Vulnerability ID | `PYSEC-2026-87` |
| Fixed version | `lxml 6.1.0` |
| Forced fixed-lxml install | Fails because `crawl4ai==0.9.0` conflicts with `lxml>=6.1.0` |
| CI posture | Dependency audit is visible but non-blocking while unresolved |

## Risk Statement

Scout cannot currently ship a clean dependency audit while keeping the upstream
Crawl4AI package. The vulnerable package is introduced by Crawl4AI's dependency
constraints, not by Scout's direct dependency choice.

The private-beta risk is acceptable only if the beta remains small, controlled,
and honest about the unresolved audit. Public launch remains blocked until the
audit is clean or a separate public-launch exception is explicitly approved.

## Recommended Private-Beta Exception

Approve a temporary exception with these controls:

1. **Beta size and access**
   - approved testers only,
   - no anonymous hosted usage,
   - no public registry install path,
   - hosted API keys remain individually provisioned and revocable.

2. **Messaging**
   - no "security clean" claim,
   - no "enterprise ready" claim,
   - no "public launch ready" claim,
   - website and docs continue to state the dependency audit blocker.

3. **Technical controls**
   - dependency-audit CI job remains visible,
   - hosted SSRF protections remain enabled,
   - hosted artifact authorization remains enforced,
   - hosted usage remains capped and metered,
   - branch-qualified local install remains the primary beta path.

4. **Operational controls**
   - record every beta expansion against this exception,
   - rerun the Crawl4AI/lxml refresh before expanding tester count,
   - review upstream Crawl4AI releases at least weekly during beta,
   - revoke or pause hosted beta access if exploitability changes or a
     practical exploit appears.

5. **Exit criteria**
   - Crawl4AI supports `lxml>=6.1.0`, or
   - Scout forks/patches/replaces the dependency path, or
   - a separate public-launch security exception is approved by a qualified
     security/legal review.

## Approval Choices

- [ ] Approve limited private-beta exception only.
- [ ] Reject exception and pause beta expansion until dependency audit is clean.
- [ ] Require deeper security review before deciding.
- [ ] Approve a stronger engineering path: fork/patch/replace Crawl4AI path.

## If Approved

Codex should:

- keep public launch blocked in `docs/product/release-checklist.md`,
- add the approval date and approver to this packet,
- update `docs/security/crawl4ai-lxml-risk-decision-2026-06-28.md`,
- keep the dependency-audit job non-blocking but visible,
- schedule or manually rerun the dependency refresh before each beta expansion.

## If Rejected

Codex should:

- keep private beta expansion blocked,
- prioritize either waiting for upstream Crawl4AI or replacing/forking the
  dependency path,
- avoid public claims that Scout is ready for broad testers.

## Explicit Non-Approval

This packet is currently **not approved**.

Until approval is recorded, the release checklist item
`Crawl4AI/lxml risk decision approved` remains open.
