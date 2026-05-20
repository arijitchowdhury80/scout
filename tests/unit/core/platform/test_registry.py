from scout.core.platform.registry import get_use_case, list_use_cases


def test_registry_lists_required_use_cases() -> None:
    use_cases = list_use_cases()

    assert "products" in use_cases
    assert "jobs" in use_cases
    assert "prism" in use_cases
    assert "investor" in use_cases
    assert "website-quality" in use_cases


def test_registry_returns_use_case_metadata() -> None:
    use_case = get_use_case("jobs")

    assert use_case.name == "jobs"
    assert "Job hunter" in use_case.description
