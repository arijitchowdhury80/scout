from scout.core.platform.targets import (
    TargetSegment,
    get_target,
    primary_targets,
    secondary_targets,
    targets_for_use_case,
)


def test_primary_target_matrix_is_balanced() -> None:
    targets = primary_targets()

    assert len(targets) == 8
    assert [target.name for target in targets] == [
        "Algolia",
        "Constructor",
        "L.L.Bean",
        "Patagonia",
        "Adobe",
        "Home Depot",
        "Estée Lauder",
        "British Airways",
    ]

    segment_counts = {segment: 0 for segment in TargetSegment}
    for target in targets:
        segment_counts[target.segment] += 1

    assert segment_counts[TargetSegment.PRIVATE_B2B_SAAS] == 2
    assert segment_counts[TargetSegment.PRIVATE_RETAIL_COMMERCE] == 2
    assert segment_counts[TargetSegment.PUBLIC_COMPANY] == 2
    assert segment_counts[TargetSegment.PUBLIC_HARD_SITE_RETAIL] == 1
    assert segment_counts[TargetSegment.PUBLIC_TRAVEL_AIRLINE] == 1


def test_secondary_targets_cover_optional_validation_companies() -> None:
    assert [target.name for target in secondary_targets()] == [
        "Nike",
        "Amplience",
        "Salesforce",
        "Intuit",
    ]


def test_use_case_target_filters_match_plan() -> None:
    assert {target.name for target in targets_for_use_case("company")} == {
        "Algolia",
        "Constructor",
        "L.L.Bean",
        "Patagonia",
        "Adobe",
        "Home Depot",
        "Estée Lauder",
        "British Airways",
    }
    assert {target.name for target in targets_for_use_case("investor")} == {
        "Adobe",
        "Home Depot",
        "Estée Lauder",
        "British Airways",
    }
    assert {target.name for target in targets_for_use_case("products", include_secondary=True)} == {
        "L.L.Bean",
        "Patagonia",
        "Home Depot",
        "Estée Lauder",
        "Nike",
    }
    assert {target.name for target in targets_for_use_case("news")} == {
        "Algolia",
        "Constructor",
        "L.L.Bean",
        "Patagonia",
        "Adobe",
        "Home Depot",
        "Estée Lauder",
        "British Airways",
    }


def test_target_lookup_supports_ascii_aliases() -> None:
    estee = get_target("Estee Lauder")
    british_airways = get_target("british-airways")
    llbean = get_target("ll bean")

    assert estee is not None
    assert estee.name == "Estée Lauder"
    assert british_airways is not None
    assert british_airways.segment == TargetSegment.PUBLIC_TRAVEL_AIRLINE
    assert llbean is not None
    assert llbean.segment == TargetSegment.PRIVATE_RETAIL_COMMERCE
