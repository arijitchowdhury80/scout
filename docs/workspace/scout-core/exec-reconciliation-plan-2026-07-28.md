# Root-Cause Fix: Exec Identity Reconciliation Layer (2026-07-28)

## Why this plan exists
Today's work added sources reactively (on-site → Wikidata → SEC → Wikipedia) and
patched symptoms one at a time. The DEF 14A golden set exposed that the residual
failures are all ONE class: **no person-identity layer.** Names arrive in
incompatible formats from each source and are merged by naive string equality, so
we get mangled names, duplicates, wrong titles, and unmeasurable quality.

Evidence (all the same root):
| Symptom | Real cause |
|---|---|
| "Ahn Luis Von" (was Luis von Ahn) | SEC LAST-FIRST reorder can't handle particles (von/van/de) |
| "Tom Killalea" ≠ "Peter Thomas Killalea"; Joe≠Joseph | no nickname / initial / suffix normalization |
| "Olivier Pomel" ×2 | dedup by exact string, not identity |
| person shown as "Director" who is CEO | titles merged flat, no authority ranking |
| Werner von Siemens (d.1892) as current | current/authority model applied ad hoc per source |
| MongoDB scored 60% (really ~90%) | the SCORER has the same name-match gap |

## Design — `scout/core/enrich/reconcile.py` (pure, fully unit-tested)

### 1. `PersonName` canonicalization  `canonical(raw:str) -> PersonName`
Handles every format seen today:
- **Reorder detection**: "COOK TIMOTHY D" / "Killalea Peter Thomas" (SEC caps LAST-FIRST)
  → First Middle Last. Detect by all-caps or comma ("Hazard, Charles M. Jr.").
- **Particles**: von, van, van der, de, del, di, la, der, den, bin, al, mac/mc —
  bind to surname so "Luis von Ahn" → given=Luis, surname="von Ahn" (fixes the mangle).
- **Suffixes**: Jr, Sr, II, III, IV, PhD, MD, Esq — stripped to a suffix field.
- **Nicknames**: small bidirectional map (Tom↔Thomas, Tim↔Timothy, Bob↔Robert,
  Bill↔William, Mike↔Michael, Chris↔Christopher, Dave↔David, Jim↔James,
  Joe↔Joseph, Dan↔Daniel, Ben↔Benjamin, Alex↔Alexander, Steve↔Stephen/Steven,
  Andy↔Andrew, Matt↔Matthew, Chuck/Charles, Ken↔Kenneth, Ron↔Ronald,
  Tony↔Anthony, Rob↔Robert, Nick↔Nicholas, Ed↔Edward, Dick↔Richard, Nate↔Nathan…).
- **Normalize**: strip accents, quotes/"nicknames", extra whitespace, case.
- Produces: `{given, middle, surname, suffix, display, key}` where `key` =
  surname + canonical-given (nickname-folded) for identity matching.

### 2. Identity match  `same_person(a:PersonName, b:PersonName) -> bool`
Surname (particle-aware) equal AND given compatible: equal, nickname-equivalent,
or initial-prefix. CONSERVATIVE — never merges different given names (never lose a
real exec). Replaces the ad-hoc `_same_person` in company.py AND the scorer's `_match`.

### 3. Authority + seniority model
- **Source authority** (for picking canonical name + title): DEF14A/SEC-officer &
  on-site-leadership = HIGH, Wikidata-structured = MEDIUM-HIGH, Wikipedia-LLM = MEDIUM.
- **Role seniority rank**: founder/CEO/chair > C-level > president/EVP/SVP >
  director/board > other. Used to pick the best title when sources disagree
  (SEC "President & CEO" beats Wikidata "Director" for the same person).

### 4. `reconcile(candidates:list[ExecCandidate]) -> list[ReconciledExec]`
- Cluster candidates by `same_person`.
- Per cluster: canonical **name** = most-complete form from the highest-authority
  source (proper case, most tokens, real surname). **Title** = highest
  seniority-rank title, tie-broken by source authority. **Confidence** = base(best
  source) boosted when ≥2 INDEPENDENT sources agree. **Provenance** = union.
- Apply current+senior filters once, centrally.
- Deterministic ordering (seniority, then name).

### 5. `ExecCandidate` contract
Each source is refactored to RETURN `list[ExecCandidate]{raw_name, title, source,
confidence}` instead of appending ExecutiveRecords. `run_company` gathers all
candidates, calls `reconcile()`, maps the result to ExecutiveRecord once.

## Also fixes the measurement
The golden scorers (`golden_score.py`, `golden_sec_score.py`) switch to
`reconcile.same_person` for matching — so MongoDB's "Tom" vs "Thomas" stops being a
false miss and the precision/recall numbers become trustworthy.

## Phases (TDD, RED→GREEN each)
1. `reconcile.py`: PersonName canonicalization + same_person + nickname/particle/
   suffix tables. ~30 unit tests covering every symptom above. **Gate: the exact
   failing pairs from today all resolve correctly.**
2. Authority/seniority + `reconcile()` cluster/merge. Unit-tested with mixed-source
   candidate fixtures.
3. Refactor sources → `ExecCandidate`; `run_company` → gather+reconcile+emit.
   Delete the scattered dedup/seen_names/`_same_person`. Full suite green.
4. Point both golden scorers at `reconcile.same_person`. Re-run SEC golden score →
   true precision/recall. Iterate reconcile until precision ≥90% / recall ≥80% on
   public cos (with the strict-floor caveat understood).

## Non-goals (explicitly deferred, not dropped)
- Last ~6% coverage (paid web-search) — separate, cost-gated.
- Products waterfall + Layer 4 ScraperAPI.
- Latency (concurrent enrichment).
These do NOT touch the identity root; they come after quality clears the bar.
