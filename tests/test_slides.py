import re
from dataclasses import asdict

import pytest

from bmpm_test.charts import build_charts
from bmpm_test.data import Case
from bmpm_test.metrics import (
    evaluate_cases,
    summarize_by_length,
    summarize_by_variant,
    summarize_overall,
)
from bmpm_test.report import CHARTS_DIR
from bmpm_test.slides import build_slides, recommendations

CASES = [
    Case("L02-01", "Ly", 2, "positive", "Li", "transliteration", ""),
    Case("L02-02", "Oz", 2, "negative", None, "unrelated", ""),
    Case("L03-01", "Kym", 3, "positive", "Kim", "transliteration", ""),
    Case("L16-01", "Hernandez Garcia", 16, "negative", None, "look_alike", ""),
]


class StubMatcher:
    answers = {"Ly": ["Li", "Lee"], "Kym": ["Lee"], "Hernandez Garcia": ["Garcia"]}

    def match(self, query):
        return self.answers.get(query, [])

    def encode(self, name):
        return frozenset({name.lower()})


def make_summary(results, **config):
    return {
        "config": {
            "name_mode": "generic", "match_mode": "approx", "concat": False,
            "abydos_version": "0.5.0", "run_at": "2026-10-22T00:00:00+00:00", **config,
        },
        "dataset": {"names": 5, "cases": len(results), "positives": 2, "negatives": 2},
        "warnings": [],
        "overall": asdict(summarize_overall(results)),
        "by_length": {str(k): asdict(s) for k, s in summarize_by_length(results).items()},
        "by_variant": {k: asdict(s) for k, s in summarize_by_variant(results).items()},
    }


@pytest.fixture
def results():
    return evaluate_cases(CASES, StubMatcher())


@pytest.fixture
def deck(tmp_path, results):
    summary = make_summary(results)
    build_charts(summary, tmp_path / CHARTS_DIR)
    path = build_slides(tmp_path, summary, results, StubMatcher().encode)
    return path, path.read_text(encoding="utf-8"), summary


def test_deck_has_eleven_slides_with_visual_and_notes(deck):
    _, text, _ = deck
    titles = re.findall(r"^## Slide (\d+): (.+)$", text, flags=re.M)
    assert [int(n) for n, _ in titles] == list(range(1, 12))
    assert titles[4][1] == "Headline results"
    assert text.count("**Visual:**") == 11
    assert text.count("**Speaker notes:**") == 11


def test_numbers_match_summary(deck):
    _, text, summary = deck
    o = summary["overall"]
    assert f"Recall {o['recall']:.1%}" in text
    assert f"Precision {o['precision']:.1%}" in text
    assert "**1 of 2** positive queries" in text
    assert "<b>" not in text


def test_chart_paths_exist(deck):
    path, text, _ = deck
    for chart in re.findall(r"`(charts/[^`]+\.png)`", text):
        assert (path.parent / chart).exists(), chart


def test_failure_examples_include_codes(deck):
    _, text, _ = deck
    assert "Missed: Kym -> expected Kim (codes kym vs kim)" in text
    assert "False match: Hernandez Garcia -> Garcia" in text


def test_recommendations_fire_on_weak_spots(results):
    recs = " ".join(recommendations(make_summary(results)))
    assert "--concat" in recs                    # length-16 negative matched
    assert "second-stage similarity" in recs     # Ly hit returned 2 names -> 50% candidate precision
    assert "--name-mode ashkenazi" in recs       # transliteration recall 50%
    assert "Review the labels of the 2 listed failures" in recs


def test_recommendations_adapt_to_config(results):
    recs = " ".join(recommendations(make_summary(results, concat=True, name_mode="sephardic")))
    assert "still over-match with concat on" in recs
    assert "Compare against `--name-mode generic`" in recs


def test_clean_run_gets_fallback_recommendation():
    clean = evaluate_cases([CASES[1]], StubMatcher())
    assert recommendations(make_summary(clean)) == [
        "No weak spots crossed the thresholds. Next, extend the test to typos and a larger name list."
    ]
