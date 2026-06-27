"""Tests for Scout benchmark artifact writer."""

import json

from scout.core.benchmark import BenchmarkResult, write_benchmark_artifacts


def test_write_benchmark_artifacts_creates_expected_files(tmp_path) -> None:
    result = BenchmarkResult(
        url="https://example.com",
        direct_http={"success": True, "duration_ms": 12, "word_count": 20, "text": "direct"},
        scout={"success": True, "duration_ms": 30, "word_count": 22, "raw_markdown": "raw", "clean_markdown": "clean"},
        recommendation="direct_http",
        reason="faster_static_page",
    )

    write_benchmark_artifacts(result, tmp_path)

    assert (tmp_path / "benchmark.json").exists()
    assert (tmp_path / "comparison.md").exists()
    assert (tmp_path / "direct_http.txt").read_text() == "direct"
    assert (tmp_path / "scout_raw.md").read_text() == "raw"
    assert (tmp_path / "scout_clean.md").read_text() == "clean"
    assert (tmp_path / "samples").is_dir()
    data = json.loads((tmp_path / "benchmark.json").read_text())
    assert data["recommendation"] == "direct_http"
    assert "# Scout acquisition benchmark" in (tmp_path / "comparison.md").read_text()
