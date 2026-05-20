"""Deterministic job-fit scoring."""

from __future__ import annotations

import re

from scout.core.use_cases.jobs import JobPostingRecord, JobSearchProfile


def _contains(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def score_job_posting(record: JobPostingRecord, profile: JobSearchProfile) -> JobPostingRecord:
    text = f"{record.title} {record.description}".lower()
    score = 0
    reasons: list[str] = []
    rejects: list[str] = []
    matched_terms = list(record.matched_terms)

    seniority_terms = profile.seniority or ["Director", "Senior Director", "VP", "Head of"]
    if any(_contains(record.title, term) for term in seniority_terms):
        score += 30
        reasons.append("Director-level role")

    desired_title_tokens = {
        token.lower()
        for title in profile.desired_titles
        for token in re.findall(r"[a-zA-Z]+", title)
        if len(token) > 2
    }
    title_hits = [token for token in desired_title_tokens if token in record.title.lower()]
    if title_hits:
        score += min(20, len(title_hits) * 5)
        reasons.append("Title matches desired role terms")
        matched_terms.extend(title_hits)

    keywords = profile.role_keywords + profile.must_have_terms + profile.required_skills
    keyword_hits = [term for term in keywords if _contains(text, term)]
    if keyword_hits:
        score += min(35, len(keyword_hits) * 8)
        reasons.append("Role keywords matched")
        matched_terms.extend(keyword_hits)

    if profile.salary_min_usd is not None:
        if record.salary_max is not None and record.salary_max >= profile.salary_min_usd:
            score += 20
            reasons.append("Compensation meets threshold")
        elif record.salary_max is not None:
            score -= 25
            rejects.append("Compensation below threshold")
        else:
            rejects.append("Compensation missing")

    reject_hits = [term for term in profile.reject_terms if _contains(text, term)]
    if reject_hits:
        score -= 35
        rejects.extend([f"Reject term matched: {term}" for term in reject_hits])

    return record.model_copy(
        update={
            "match_score": _clamp(score),
            "match_reasons": _unique(reasons),
            "reject_reasons": _unique(rejects),
            "matched_terms": _unique(matched_terms),
        }
    )
