"""End-to-end run on data/sample/ with real abydos.

Outcomes are pinned per case so a library upgrade that changes matching
behaviour fails here instead of silently shifting the report.
"""

import csv
import json
from pathlib import Path

import pytest

from bmpm_test.cli import main

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"

PER_WORD_OUTCOMES = {
    "L02-01": "TP", "L02-02": "TN", "L03-01": "TP", "L03-02": "TP", "L03-03": "TN",
    "L05-01": "TP", "L05-02": "TP", "L05-03": "TP", "L06-01": "TN", "L07-01": "FN",
    "L07-02": "TN", "L08-01": "FN", "L08-02": "TP", "L08-03": "TN", "L09-01": "TP",
    "L09-02": "FN", "L09-03": "TN", "L10-01": "TP", "L10-02": "TP", "L12-01": "TP",
    "L15-01": "TP", "L19-01": "FP", "L19-02": "TP", "L21-01": "TP",
}


def run_sample(out: Path, *extra: str) -> list[dict]:
    args = ["--names", str(SAMPLE / "names.csv"), "--cases", str(SAMPLE / "test_cases.csv"),
            "--out", str(out), "--allow-uneven", *extra]
    assert main(args) == 0
    with open(out / "artifact 1.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def per_word(tmp_path_factory):
    out = tmp_path_factory.mktemp("per_word")
    return out, run_sample(out)


def test_all_outputs_written(per_word):
    out, _ = per_word
    for name in ("artifact 1.csv", "artifact 2.json", "artifact 3.pdf", "artifact 4.md"):
        assert (out / name).stat().st_size > 0, name
    assert (out / "artifact 3.pdf").read_bytes().startswith(b"%PDF")


def test_per_word_outcomes_are_pinned(per_word):
    _, rows = per_word
    assert {r["case_id"]: r["outcome"] for r in rows} == PER_WORD_OUTCOMES


def test_per_word_overmatches_compounds(per_word):
    _, rows = per_word
    by_id = {r["case_id"]: r for r in rows}
    assert by_id["L19-01"]["candidates"].split("|") == [
        "Rodriguez", "Hernandez Cruz", "Rodriguez-Lopez", "Rodriguez-Hernandez",
    ]


def test_summary_totals(per_word):
    out, _ = per_word
    overall = json.loads((out / "artifact 2.json").read_text(encoding="utf-8"))["overall"]
    assert (overall["tp"], overall["fn"], overall["fp"], overall["tn"]) == (14, 3, 1, 6)


def test_concat_removes_compound_false_positive(tmp_path):
    rows = {r["case_id"]: r for r in run_sample(tmp_path, "--concat")}
    assert rows["L19-01"]["outcome"] == "TN"
    assert rows["L12-01"]["candidates"] == "Garcia-Lopez"
    assert rows["L21-01"]["candidates"] == "Vladislav Tchaikovsky"
