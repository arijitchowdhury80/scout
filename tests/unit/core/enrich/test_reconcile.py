"""Identity reconciliation — canonicalization + same_person. Each test targets a
concrete failure the DEF 14A golden set exposed on 2026-07-28."""

from __future__ import annotations

from scout.core.enrich.reconcile import canonical, same_name, same_person


# --- reorder (SEC LAST-FIRST) -------------------------------------------------
def test_sec_allcaps_last_first_reorder() -> None:
    p = canonical("COOK TIMOTHY D")
    assert p.given.startswith("Timothy")
    assert p.surname == "Cook"
    assert p.display == "Timothy D Cook"


def test_comma_last_first_with_suffix() -> None:
    p = canonical("Hazard, Charles M. Jr.")
    assert p.surname == "Hazard"
    assert p.given.startswith("Charles")
    assert p.suffix == "Jr"


# --- particles (the "Ahn Luis Von" mangle) ------------------------------------
def test_particle_surname_not_reordered() -> None:
    p = canonical("Luis von Ahn")
    assert p.surname == "von Ahn"
    assert p.given == "Luis"
    assert p.display == "Luis von Ahn"  # NOT "Ahn Luis Von"


def test_van_der_particle() -> None:
    p = canonical("Jan van der Berg")
    assert p.surname == "van der Berg"
    assert p.given == "Jan"


# --- identity matching: the exact golden-set false misses ---------------------
def test_nickname_tom_thomas() -> None:
    assert same_name("Tom Killalea", "Peter Thomas Killalea")  # Tom<->Thomas, extra middle
    assert same_name("Thomas Killalea", "Tom Killalea")


def test_apostrophe_and_accents() -> None:
    assert same_name("Francisco D'Souza", "Francisco Dsouza")
    assert same_name("José Ramón", "Jose Ramon")


def test_suffix_placement() -> None:
    assert same_name("Charles M. Hazard, Jr.", "Charles M Jr Hazard")


def test_initial_prefix() -> None:
    assert same_name("Tim Cook", "Timothy Cook")
    assert same_name("T. Cook", "Timothy Cook")
    assert same_name("Andrew Bonfield", "Andrew R.J. Bonfield")


def test_exact_duplicate() -> None:
    assert same_name("Olivier Pomel", "Olivier Pomel")


# --- CONSERVATIVE: never merge different people (never lose a real exec) -------
def test_different_given_not_merged() -> None:
    assert not same_name("John Smith", "Jane Smith")
    assert not same_name("Georg von Siemens", "Werner von Siemens")


def test_different_surname_not_merged() -> None:
    assert not same_name("Olivier Pomel", "Amit Agarwal")


def test_nickname_joe_joseph_now_matches() -> None:
    # Joe<->Joseph via the nickname table (prefix alone could not do this).
    assert same_name("Joe Creed", "Joseph Creed")


# --- robustness ---------------------------------------------------------------
def test_empty_and_junk() -> None:
    assert canonical("").key == ""
    assert not same_name("", "Tim Cook")
    assert not same_name("   ", "")


def test_quoted_nickname_stripped() -> None:
    p = canonical('Chirantan "CJ" Desai')
    assert p.surname == "Desai"
    assert p.given == "Chirantan"
    assert same_name('Chirantan "CJ" Desai', "Chirantan J. Desai")


def test_single_name_no_crash() -> None:
    p = canonical("Madonna")
    assert p.display  # doesn't crash; some key produced


# --- Phase 2: reconcile() cluster-merge ---------------------------------------
from scout.core.enrich.reconcile import ExecCandidate, reconcile, _seniority_rank  # noqa: E402


def test_seniority_ranking() -> None:
    assert _seniority_rank("Chief Executive Officer") > _seniority_rank("CFO")
    assert _seniority_rank("Founder") > _seniority_rank("Director")
    assert _seniority_rank("CFO") > _seniority_rank("SVP, Product")
    assert _seniority_rank("Director") > _seniority_rank("")


def test_reconcile_merges_cross_source_same_person_best_title_wins() -> None:
    cands = [
        ExecCandidate(raw_name="POMEL OLIVIER", title="Director", source="sec"),  # SEC caps
        ExecCandidate(raw_name="Olivier Pomel", title="CEO & Co-Founder", source="onsite"),
        ExecCandidate(raw_name="Olivier Pomel", title="", source="wikidata"),
    ]
    out = reconcile(cands)
    assert len(out) == 1  # one person, not three
    assert out[0].name == "Olivier Pomel"  # reordered from SEC caps
    assert "CEO" in out[0].title  # most senior title wins over "Director"
    assert set(out[0].sources) == {"sec", "onsite", "wikidata"}
    assert out[0].confidence >= 0.7  # boosted by multi-source agreement


def test_reconcile_nickname_and_middle_name_cluster() -> None:
    cands = [
        ExecCandidate(raw_name="Tom Killalea", title="Chairperson", source="sec"),
        ExecCandidate(raw_name="Peter Thomas Killalea", title="Director", source="wikidata"),
    ]
    out = reconcile(cands)
    assert len(out) == 1  # Tom == Thomas (middle name)
    assert out[0].title == "Chairperson"  # chair outranks director


def test_reconcile_keeps_distinct_people() -> None:
    cands = [
        ExecCandidate(raw_name="John Smith", title="CEO", source="onsite"),
        ExecCandidate(raw_name="Jane Smith", title="CFO", source="onsite"),
    ]
    out = reconcile(cands)
    assert len(out) == 2  # never merge different first names


def test_reconcile_orders_leadership_first() -> None:
    cands = [
        ExecCandidate(raw_name="Ann Director", title="Director", source="sec"),
        ExecCandidate(raw_name="Bob Boss", title="Chief Executive Officer", source="onsite"),
    ]
    out = reconcile(cands)
    assert out[0].name == "Bob Boss"  # CEO before director
