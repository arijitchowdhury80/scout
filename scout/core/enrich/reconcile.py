"""Exec identity reconciliation — the root fix for unreliable exec extraction.

Every exec source (on-site, Wikidata, SEC, Wikipedia) emits names/titles in a
DIFFERENT format. Merging them by naive string equality caused the whole class of
bugs the DEF 14A golden set exposed: mangled names ("Luis von Ahn" -> "Ahn Luis
Von"), duplicates ("Olivier Pomel" x2), unmatched identities ("Tom Killalea" vs
"Peter Thomas Killalea"), wrong titles ("Director" for a CEO), and even wrong
MEASUREMENT.

This module is the single place identity is resolved:
  1. canonical(raw)  -> PersonName   (reorder / particles / suffixes / nicknames)
  2. same_person(a,b)                (conservative identity match)
  3. reconcile(candidates) -> [ReconciledExec]  (cluster + authority-merge)

Pure and fully unit-tested; sources feed it, run_company and the golden scorers
both use it, so product and measurement share one notion of identity.
"""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel

# --- source authority (higher = more trusted for canonical name + title) ------
SOURCE_AUTHORITY: dict[str, int] = {
    "onsite": 5,  # the company's own current leadership page
    "sec": 5,  # SEC filings — authoritative for public-co officers/directors
    "wikidata": 3,
    "wikipedia": 2,
}

# --- nickname folding: map both directions to a canonical root ----------------
_NICKNAME_GROUPS: list[tuple[str, ...]] = [
    ("thomas", "tom", "tommy"),
    ("timothy", "tim"),
    ("robert", "rob", "bob", "bobby"),
    ("william", "will", "bill", "billy"),
    ("michael", "mike", "mick"),
    ("christopher", "chris"),
    ("david", "dave"),
    ("james", "jim", "jimmy", "jamie"),
    ("joseph", "joe", "joey"),
    ("daniel", "dan", "danny"),
    ("benjamin", "ben"),
    ("alexander", "alex"),
    ("stephen", "steven", "steve"),
    ("andrew", "andy", "drew"),
    ("matthew", "matt"),
    ("charles", "chuck", "charlie"),
    ("kenneth", "ken"),
    ("ronald", "ron"),
    ("anthony", "tony"),
    ("nicholas", "nick"),
    ("edward", "ed", "eddie", "ted"),
    ("richard", "rick", "rich", "dick"),
    ("nathaniel", "nathan", "nate"),
    ("jonathan", "jon", "jonny"),
    ("samuel", "sam"),
    ("patrick", "pat"),
    ("gregory", "greg"),
    ("jeffrey", "jeff"),
    ("kevin", "kev"),
    ("elizabeth", "liz", "beth", "eliza"),
    ("katherine", "kate", "katie", "kathy", "catherine"),
    ("margaret", "maggie", "meg", "peggy"),
    ("jennifer", "jen", "jenny"),
    ("deborah", "deb", "debbie"),
    ("rebecca", "becca", "becky"),
    ("susan", "sue", "suzy"),
]
_NICK_TO_ROOT: dict[str, str] = {n: g[0] for g in _NICKNAME_GROUPS for n in g}

# surname particles that bind to the surname, not a middle name ----------------
_PARTICLES = {
    "von",
    "van",
    "der",
    "den",
    "de",
    "del",
    "della",
    "di",
    "da",
    "la",
    "le",
    "el",
    "al",
    "bin",
    "ibn",
    "mac",
    "mc",
    "st",
    "st.",
    "ter",
    "ten",
    "op",
}
_SUFFIXES = {
    "jr",
    "jr.",
    "sr",
    "sr.",
    "ii",
    "iii",
    "iv",
    "v",
    "phd",
    "ph.d.",
    "md",
    "m.d.",
    "esq",
    "esq.",
}


class PersonName(BaseModel):
    given: str = ""
    surname: str = ""
    suffix: str = ""
    display: str = ""  # best human-readable form of the input
    surname_key: str = ""  # normalized surname (particle-aware, no punctuation)
    given_roots: tuple[str, ...] = ()  # nickname-folded roots of real given tokens (len>1)
    first_given: str = ""  # folded first given token (may be a single initial)

    model_config = {"frozen": True}

    @property
    def key(self) -> str:
        """Human-debuggable identity key (not used for matching)."""
        return f"{self.first_given}|{self.surname_key}" if self.surname_key else self.first_given


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _fold(token: str) -> str:
    """Nickname-fold a given-name token to its canonical root for matching."""
    t = token.lower().strip(".")
    return _NICK_TO_ROOT.get(t, t)


_SUFFIX_RE = re.compile(r",?\s*\b(jr|sr|ii|iii|iv|phd|md|esq)\b\.?", re.I)


def canonical(raw: str) -> PersonName:
    """Parse a raw name (any source format) into a normalized PersonName.

    Handles SEC 'LAST FIRST MIDDLE' (all-caps or comma), surname particles
    (von/van/de...), suffixes (Jr/III/PhD), nickname quotes, and accents.
    """
    if not raw or not raw.strip():
        return PersonName()
    text = _strip_accents(raw).strip()
    text = re.sub(r'"[^"]*"|\([^)]*\)', " ", text)  # drop "CJ" / (nick)
    text = text.replace("'", "").replace("`", "")  # D'Souza -> DSouza (join, don't split)

    # Pull the suffix out FIRST (with any leading comma) so a trailing "…, Jr."
    # can't be mistaken for a 'Surname, Given' last-first comma.
    suffix = ""
    sm = _SUFFIX_RE.search(text)
    if sm:
        suffix = sm.group(1)
        text = _SUFFIX_RE.sub(" ", text)

    comma = "," in text
    text = re.sub(r"[^A-Za-z.\-\s,]", " ", text)
    tokens = [t for t in re.split(r"[\s,]+", text) if t and t not in ("-", ".")]
    if not tokens:
        return PersonName()

    all_caps = len(tokens) >= 2 and all(t.isupper() for t in tokens if t.isalpha())
    last_first = comma or all_caps
    lower = [t.lower() for t in tokens]

    if last_first:
        surname_tokens = [tokens[0]]
        given_tokens = tokens[1:]
    else:
        # First Middle ... Last, with leading particles gluing to the surname.
        surname_start = len(tokens) - 1
        for i in range(len(tokens) - 1):
            if lower[i] in _PARTICLES:
                surname_start = i
                break
        given_tokens = tokens[:surname_start]
        surname_tokens = tokens[surname_start:]

    def _title(words: list[str]) -> str:
        return " ".join(w.lower() if w.lower() in _PARTICLES else w.capitalize() for w in words)

    given_d = _title(given_tokens)
    surname_d = _title(surname_tokens)
    display = " ".join(p for p in [given_d, surname_d] if p)
    if suffix:
        display = f"{display} {suffix.capitalize()}"

    surname_key = re.sub(r"[^a-z]", "", "".join(surname_tokens).lower())
    real_given = [t.strip(".") for t in given_tokens if len(t.strip(".")) > 1]
    given_roots = tuple(dict.fromkeys(_fold(t) for t in real_given))
    first_given = _fold(given_tokens[0]) if given_tokens else ""

    return PersonName(
        given=given_d,
        surname=surname_d,
        suffix=suffix.capitalize(),
        display=display,
        surname_key=surname_key,
        given_roots=given_roots,
        first_given=first_given,
    )


def same_person(a: PersonName, b: PersonName) -> bool:
    """Conservative identity match: surnames equal AND some given name compatible.

    Compatible = a shared folded root ANYWHERE in the given names (so 'Tom' matches
    the middle name in 'Peter Thomas Killalea'), OR the first-given tokens are
    equal / initial-prefix compatible. Never merges two distinct given names, so a
    real exec is never lost to a merge.
    """
    if not a.surname_key or not b.surname_key or a.surname_key != b.surname_key:
        return False
    ra, rb = set(a.given_roots), set(b.given_roots)
    if ra and rb and (ra & rb):
        return True
    fa, fb = a.first_given, b.first_given
    if not fa or not fb:
        return True  # same surname, one side has no usable given -> treat as same
    if fa == fb:
        return True
    return fa.startswith(fb) or fb.startswith(fa)


def same_name(a: str, b: str) -> bool:
    """Convenience: identity match on two RAW name strings."""
    return same_person(canonical(a), canonical(b))


# --- authority + seniority + the reconcile() merge ----------------------------
class ExecCandidate(BaseModel):
    """One exec as claimed by ONE source, pre-reconciliation."""

    raw_name: str
    title: str = ""
    source: str = "onsite"  # key into SOURCE_AUTHORITY
    confidence: float = 0.6
    profile_url: str = ""
    source_url: str = ""


class ReconciledExec(BaseModel):
    """One person after clustering identical candidates across sources."""

    name: str
    title: str = ""
    sources: list[str] = []
    confidence: float = 0.0
    profile_url: str = ""
    source_url: str = ""
    seniority: int = 0


def _seniority_rank(title: str) -> int:
    """Rank a title so the most senior role wins when sources disagree, and the
    output can be ordered leadership-first."""
    t = title.lower()
    if "chief executive" in t or re.search(r"\bceo\b", t):
        return 100
    if "founder" in t:
        return 95
    if "president" in t and "vice" not in t:
        return 88
    if "chair" in t:
        return 86
    if re.search(r"\bchief\b", t) or re.search(r"\bc[a-z]{1,2}o\b", t):
        return 82  # other C-level (CFO/CTO/COO/CMO/CRO/CPO…)
    if re.search(r"\b(evp|svp|executive vice president|senior vice president)\b", t):
        return 60
    if re.search(r"\bvp\b|vice president", t):
        return 50
    if "director" in t or "board" in t:
        return 40
    return 20


def _authority(source: str) -> int:
    return SOURCE_AUTHORITY.get(source, 1)


def reconcile(candidates: list[ExecCandidate]) -> list[ReconciledExec]:
    """Cluster candidates that refer to the same person and merge each cluster
    into one canonical record.

    Per cluster: canonical NAME = the fullest form from the highest-authority
    source; TITLE = the highest-seniority title (tie-broken by source authority);
    CONFIDENCE = the best candidate's confidence, boosted when >=2 DISTINCT
    sources agree (independent corroboration); PROVENANCE = all sources. Output is
    ordered leadership-first (seniority, then name)."""
    clusters: list[list[tuple[ExecCandidate, PersonName]]] = []
    for cand in candidates:
        pn = canonical(cand.raw_name)
        if not pn.surname_key and not pn.first_given:
            continue  # unparseable name -> drop
        placed = False
        for cluster in clusters:
            if same_person(pn, cluster[0][1]):
                cluster.append((cand, pn))
                placed = True
                break
        if not placed:
            clusters.append([(cand, pn)])

    out: list[ReconciledExec] = []
    for cluster in clusters:
        # canonical display name: highest (authority, name-completeness)
        best_name = max(
            cluster,
            key=lambda cp: (_authority(cp[0].source), len(cp[1].given_roots), len(cp[1].display)),
        )[1].display
        # best title: highest seniority, then source authority, then longer/specific
        titled = [cp for cp in cluster if cp[0].title.strip()]
        if titled:
            best = max(
                titled,
                key=lambda cp: (
                    _seniority_rank(cp[0].title),
                    _authority(cp[0].source),
                    len(cp[0].title),
                ),
            )
            title = best[0].title.strip()
            seniority = _seniority_rank(title)
        else:
            title, seniority = "", 20
        sources = sorted({cp[0].source for cp in cluster})
        base = max(cp[0].confidence for cp in cluster)
        confidence = round(min(base + (0.1 if len(sources) >= 2 else 0.0), 0.99), 2)
        prof = next((cp[0].profile_url for cp in cluster if cp[0].profile_url), "")
        src_url = max(cluster, key=lambda cp: _authority(cp[0].source))[0].source_url
        out.append(
            ReconciledExec(
                name=best_name,
                title=title,
                sources=sources,
                confidence=confidence,
                profile_url=prof,
                source_url=src_url,
                seniority=seniority,
            )
        )
    out.sort(key=lambda e: (-e.seniority, e.name))
    return out
