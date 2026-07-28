"""MOAT Layer 2 — leadership-page link discovery ranking. Pure functions, no
network. Verified against live findings 2026-07-27 (Anthropic's /company is only
reachable via nav-harvest; Datadog's sitemap buries /leadership under 213 press
releases)."""

from scout.core.use_cases.runners.company import (
    _discover_leadership_urls,
    _extract_anchor_candidates,
    _leadership_score,
    _leadership_text_score,
    _prefilter_candidates,
)

BASE = "https://www.acme.com"


def test_prefilter_consumes_url_text_and_emits_text_url() -> None:
    """Regression: _extract_anchor_candidates emits (url, text); the LLM selector
    wants (text, url). A tuple-order mismatch here silently dropped EVERY nav
    anchor (its 'url' was actually link text, failing the http check), leaving
    only sitemap noise — the GitLab 0-execs bug."""
    anchors = [
        ("https://www.acme.com/company/team", "Leadership"),  # (url, text) as emitted
        ("https://www.acme.com/pricing", "Pricing"),
    ]
    out = _prefilter_candidates(BASE, anchors, sitemap_urls=[])
    # emitted as (anchor_text, url); leadership candidate ranked first
    assert out[0] == ("Leadership", "https://www.acme.com/company/team")
    assert all(url.startswith("http") for _, url in out)  # url is really the url


def test_prefilter_ranks_leadership_above_sitemap_noise() -> None:
    """The real team link must survive the cap even when sitemap noise is huge —
    the Figma repro (300 color-swatch pages burying the about link)."""
    anchors = [("https://www.acme.com/leadership", "Leadership")]
    sitemap_noise = [f"https://www.acme.com/colors/shade-{i}" for i in range(200)]
    out = _prefilter_candidates(BASE, anchors, sitemap_noise, limit=5)
    assert out[0] == ("Leadership", "https://www.acme.com/leadership")


def test_prefilter_drops_foreign_host_and_excluded() -> None:
    anchors = [
        ("https://linkedin.com/company/acme", "Acme on LinkedIn"),
        ("https://www.acme.com/blog/leadership-post", "Leadership"),  # excluded segment
        ("https://www.acme.com/team", "Team"),
    ]
    out = _prefilter_candidates(BASE, anchors, [])
    assert out == [("Team", "https://www.acme.com/team")]


def test_anchor_text_scoring() -> None:
    assert _leadership_text_score("Leadership") == 3
    assert _leadership_text_score("Meet the team") == 3  # -> meet-the-team (strong)
    assert _leadership_text_score("Our People") == 3  # -> our-people (strong)
    assert _leadership_text_score("Company") == 1  # medium
    assert _leadership_text_score("Pricing") == 0
    assert _leadership_text_score("") == 0


def test_anchor_text_rescues_keywordless_url() -> None:
    """A nav link that SAYS 'Leadership' but points to a cryptic URL still ranks
    — the DOM-native version of the 'read the nav' idea."""
    candidates = [
        ("https://www.acme.com/x7f2", "Leadership"),  # cryptic url, strong text
        ("https://www.acme.com/pricing", "Pricing"),
    ]
    assert _discover_leadership_urls(BASE, candidates, limit=1) == ["https://www.acme.com/x7f2"]


def test_anchor_text_cannot_rescue_excluded_url() -> None:
    """Strong link text must NOT pull in a blog/press URL."""
    candidates = [("https://www.acme.com/blog/new-leadership-hire", "Leadership")]
    assert _discover_leadership_urls(BASE, candidates) == []


def test_extract_anchor_candidates_parses_href_and_text() -> None:
    html = (
        '<nav><a href="/company">Company</a>'
        '<a href="https://www.acme.com/leadership"> Our Leadership </a>'
        "<a>no href</a></nav>"
    )
    pairs = _extract_anchor_candidates(html, BASE)
    assert ("https://www.acme.com/company", "Company") in pairs
    assert ("https://www.acme.com/leadership", "Our Leadership") in pairs
    assert len(pairs) == 2  # the anchor without href is skipped


def test_strong_segment_outscores_medium() -> None:
    assert _leadership_score("https://www.acme.com/leadership") == 3
    assert _leadership_score("https://www.acme.com/company") == 1
    assert _leadership_score("https://www.acme.com/about/leadership") == 3


def test_excluded_segment_rejected_even_if_keyword_matches() -> None:
    # datadog repro: /about/latest-news/press-releases/... matches "about" but
    # must be rejected as press-release noise.
    assert _leadership_score("https://www.acme.com/about/latest-news/press-releases/x") == 0
    assert _leadership_score("https://www.acme.com/blog/our-team-culture") == 0
    assert _leadership_score("https://www.acme.com/careers/team-lead") == 0
    assert _leadership_score("https://www.acme.com/investors/board") == 0


def test_non_leadership_url_scores_zero() -> None:
    assert _leadership_score("https://www.acme.com/products/widget") == 0
    assert _leadership_score("https://www.acme.com/") == 0


def test_discovery_prefers_strong_then_shallow() -> None:
    urls = [
        "https://www.acme.com/company",  # medium, depth 1
        "https://www.acme.com/about/leadership",  # strong, depth 2
        "https://www.acme.com/our-team",  # strong, depth 1
    ]
    ranked = _discover_leadership_urls(BASE, urls, limit=3)
    assert ranked[0] == "https://www.acme.com/our-team"  # strong + shallowest
    assert ranked[1] == "https://www.acme.com/about/leadership"  # strong, deeper
    assert ranked[2] == "https://www.acme.com/company"  # medium


def test_discovery_is_same_host_only() -> None:
    urls = [
        "https://www.linkedin.com/company/acme",  # foreign host — drop
        "https://twitter.com/acme",  # foreign host — drop
        "https://www.acme.com/leadership",
    ]
    assert _discover_leadership_urls(BASE, urls) == ["https://www.acme.com/leadership"]


def test_discovery_excludes_homepage_itself_and_dedupes() -> None:
    urls = [
        "https://www.acme.com",  # homepage — drop
        "https://www.acme.com/leadership",
        "https://www.acme.com/leadership/",  # dup (trailing slash)
    ]
    assert _discover_leadership_urls(BASE, urls) == ["https://www.acme.com/leadership"]


def test_anthropic_repro_company_link_wins_when_only_candidate() -> None:
    """Anthropic: nav exposes /company (the only roster path); sitemap omits it."""
    homepage_links = [
        "https://www.anthropic.com/pricing",
        "https://www.anthropic.com/company",
        "https://claude.com/programs/x",  # foreign host
        "https://www.linkedin.com/company/anthropicresearch",  # foreign host
    ]
    ranked = _discover_leadership_urls("https://www.anthropic.com", homepage_links)
    assert ranked == ["https://www.anthropic.com/company"]


def test_nav_link_wins_over_sitemap_on_tie() -> None:
    """Passed homepage-links-first, a nav link outranks an equal-score sitemap
    entry (stable ordering)."""
    nav = ["https://www.acme.com/team"]
    sitemap = ["https://www.acme.com/people"]  # both medium(1)? team & people both medium
    ranked = _discover_leadership_urls(BASE, [*nav, *sitemap], limit=1)
    assert ranked == ["https://www.acme.com/team"]
