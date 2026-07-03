from scout.core.platform.registry import get_use_case, list_use_cases


def test_registry_lists_required_use_cases() -> None:
    use_cases = list_use_cases()

    assert "products" in use_cases
    assert "jobs" not in use_cases
    assert "careers" in use_cases
    assert "prism" in use_cases
    assert "investor" in use_cases
    assert "website-quality" not in use_cases
    assert "locations" in use_cases


def test_registry_returns_use_case_metadata() -> None:
    use_case = get_use_case("careers")

    assert use_case.name == "careers"
    assert "hiring signals" in use_case.description


def test_registry_rejects_removed_low_value_use_cases() -> None:
    assert get_use_case("website-quality") is None
    assert get_use_case("jobs") is None
