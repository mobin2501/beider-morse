"""Write presentation.md: slide-by-slide content for building a deck by hand.

Every number comes from the same ``summary`` dict as report.pdf, so the deck and
the report never disagree. Chart paths are relative to presentation.md.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from pathlib import Path

from bmpm_test.charts import CANDIDATES_CHART, RECALL_FPR_CHART, false_positive_rate
from bmpm_test.metrics import FN, FP, CaseResult
from bmpm_test.report import CHARTS_DIR, num, pct, takeaway

SLIDES_FILE = "presentation.md"

MAX_EXAMPLES = 3
MAX_LISTED = 4

# Recommendation thresholds.
LOW_RECALL = 0.8
HIGH_FPR = 0.5
LOW_CANDIDATE_PRECISION = 0.8
LONG_QUERY = 15


def md_bold(text: str) -> str:
    return f"**{text}**"


def _listed(items, limit: int = MAX_LISTED) -> str:
    items = list(items)
    if not items:
        return "(none)"
    shown = ", ".join(items[:limit])
    return shown if len(items) <= limit else f"{shown} +{len(items) - limit} more"


def _slide(number: int, title: str, bullets: list[str], visual: str, notes: str) -> str:
    lines = [f"## Slide {number}: {title}", ""]
    lines += [f"- {b}" for b in bullets]
    lines += ["", f"**Visual:** {visual}", "", f"**Speaker notes:** {notes}", ""]
    return "\n".join(lines)


def _chart_ref(filename: str) -> str:
    return f"`{CHARTS_DIR}/{filename}`"


def _length_extremes(summary: dict, key: str) -> tuple[tuple[float, int], tuple[float, int]] | None:
    values = [(s[key], int(k)) for k, s in summary["by_length"].items() if s[key] is not None]
    if not values:
        return None
    return min(values), max(values)


def _fpr_by_length(summary: dict) -> list[tuple[float, int]]:
    return [
        (false_positive_rate(s["specificity"]), int(k))
        for k, s in summary["by_length"].items()
        if s["specificity"] is not None
    ]


def recommendations(summary: dict) -> list[str]:
    config, overall = summary["config"], summary["overall"]
    recs = []

    long_fprs = [(fpr, length) for fpr, length in _fpr_by_length(summary) if length >= LONG_QUERY]
    if long_fprs:
        worst_fpr, worst_len = max(long_fprs)
        if worst_fpr >= HIGH_FPR:
            if not config["concat"]:
                recs.append(
                    f"Long queries over-match (false-positive rate {pct(worst_fpr)} at length {worst_len}). "
                    "Re-run with `--concat` so compound names only match whole compounds."
                )
            else:
                recs.append(
                    f"Long queries still over-match with concat on (false-positive rate {pct(worst_fpr)} at "
                    f"length {worst_len}). Add a second-stage check, such as edit distance, before accepting a match."
                )

    cand_precision = overall["candidate_precision"]
    if cand_precision is not None and cand_precision < LOW_CANDIDATE_PRECISION:
        recs.append(
            f"The intended name made up only {pct(cand_precision)} of returned names on hits. Rank candidates "
            "with a second-stage similarity score (e.g. edit distance or Jaro-Winkler) instead of accepting all."
        )

    translit = summary["by_variant"].get("transliteration")
    if translit and translit["recall"] is not None and translit["recall"] < LOW_RECALL:
        if config["name_mode"] == "generic":
            recs.append(
                f"Transliteration recall is {pct(translit['recall'])}. Try `--name-mode ashkenazi` or "
                "`--name-mode sephardic` if the names come mainly from those traditions."
            )
        else:
            recs.append(f"Transliteration recall is {pct(translit['recall'])}. Compare against `--name-mode generic`.")

    if config["match_mode"] == "exact" and overall["recall"] is not None and overall["recall"] < LOW_RECALL:
        recs.append(f"Recall is {pct(overall['recall'])} in exact mode. Compare against `--match-mode approx`.")

    if overall["fn"] or overall["fp"]:
        recs.append(
            f"Review the labels of the {overall['fn'] + overall['fp']} listed failures in report.pdf. "
            "Some may be ground-truth errors rather than BMPM errors."
        )
    if not recs:
        recs.append("No weak spots crossed the thresholds. Next, extend the test to typos and a larger name list.")
    return recs


def build_slides(
    out_dir: Path,
    summary: dict,
    results: list[CaseResult],
    encode: Callable[[str], frozenset[str]],
) -> Path:
    """Write presentation.md into ``out_dir``; return its path."""
    config, dataset, overall = summary["config"], summary["dataset"], summary["overall"]
    word_mode = "concat (whole-name)" if config["concat"] else "per-word (library default)"
    lengths = sorted(int(k) for k in summary["by_length"])
    span = f"{lengths[0]}-{lengths[-1]}" if lengths else "n/a"
    slides = []

    slides.append(_slide(
        1, "Beider-Morse Phonetic Matching: accuracy test",
        [
            f"Run {config['run_at']}",
            f"abydos {config['abydos_version']}: name mode {config['name_mode']}, "
            f"match mode {config['match_mode']}, {word_mode} encoding",
            f"{dataset['names']} reference names, {dataset['cases']} labeled queries",
        ],
        "Title slide.",
        "This deck summarizes how accurately BMPM matches names by sound. Full details are in report.pdf.",
    ))

    slides.append(_slide(
        2, "The question",
        [
            "When a name is spelled differently but sounds the same, does BMPM find it?",
            "When a name sounds different from everything on the list, does BMPM correctly return nothing?",
            f"Does accuracy change with name length ({span} characters)?",
        ],
        "Three short statements, no chart.",
        "We measure accuracy only, not speed. Typos are out of scope because BMPM matches sounds, not keystrokes.",
    ))

    slides.append(_slide(
        3, "Method",
        [
            "A query matches a list name when their BMPM phonetic code sets share at least one code",
            "Positive case: hit (TP) if the intended name is among the results, otherwise a miss (FN)",
            "Negative case: false positive (FP) if any name is returned, otherwise correct (TN)",
            f"Multi-word names encoded {word_mode}",
        ],
        "Simple flow: query -> BMPM codes -> look up list names sharing a code -> score the outcome.",
        "Extra names returned on a positive case are not counted as false positives; slide 7 covers them "
        "separately as over-matching.",
    ))

    variants = Counter((r.case_type, r.variant_type) for r in results)
    variant_table = "Table: " + "; ".join(f"{vt} ({ct}) {n}" for (ct, vt), n in sorted(variants.items()))
    slides.append(_slide(
        4, "Dataset",
        [
            f"{dataset['names']} reference names across lengths {span}",
            f"{dataset['cases']} queries: {dataset['positives']} positive, {dataset['negatives']} negative",
            "Positives are spelling variants, transliterations or phonetic respellings of a list name",
            "Negatives are look-alikes or unrelated names that should match nothing",
        ],
        variant_table + ".",
        "The names and labeled queries were generated by an LLM and checked by the validator before the run.",
    ))

    slides.append(_slide(
        5, "Headline results",
        [
            f"Recall {pct(overall['recall'])}",
            f"Precision {pct(overall['precision'])}",
            f"F1 {pct(overall['f1'])}",
            f"Specificity {pct(overall['specificity'])}",
            f"Accuracy {pct(overall['accuracy'])}",
        ],
        "Five KPI tiles in a row, one number each.",
        takeaway(summary, bold=md_bold),
    ))

    recall_ext = _length_extremes(summary, "recall")
    fprs = _fpr_by_length(summary)
    length_bullets = []
    if recall_ext:
        (low, low_len), (high, _) = recall_ext
        scored = [s["recall"] for s in summary["by_length"].values() if s["recall"] is not None]
        at_high = sum(r == high for r in scored)
        length_bullets.append(f"Lowest recall: length {low_len} ({pct(low)}); "
                              f"highest recall {pct(high)} at {at_high} of {len(scored)} lengths")
    if fprs:
        worst_fpr, fpr_len = max(fprs)
        length_bullets.append(f"Highest false-positive rate: length {fpr_len} ({pct(worst_fpr)})")
    length_bullets.append("Each length has only a few queries, so one case moves a rate a lot; read the trend")
    slides.append(_slide(
        6, "Accuracy by query length", length_bullets,
        f"Line chart {_chart_ref(RECALL_FPR_CHART)} (recall and false-positive rate on one 0-100% axis).",
        "Point out where the two lines diverge. Long names generate many alternative codes, which raises "
        "the chance of an accidental match.",
    ))

    cand_ext = _length_extremes(summary, "mean_candidates")
    over_bullets = [
        f"{num(overall['mean_candidates'])} names returned per query on average",
        f"When the intended name was found, it made up {pct(overall['candidate_precision'])} of the results "
        "(100% = only match)",
    ]
    if cand_ext:
        _, (peak, peak_len) = cand_ext
        over_bullets.append(f"Most names returned at length {peak_len} ({num(peak)} per query)")
    slides.append(_slide(
        7, "Over-matching", over_bullets,
        f"Column chart {_chart_ref(CANDIDATES_CHART)}.",
        "BMPM returns every list name that shares a code, so in practice it is a candidate generator. "
        "A downstream step still has to choose among the candidates.",
    ))

    variant_bullets = []
    for name, s in summary["by_variant"].items():
        if s["tp"] + s["fn"]:
            variant_bullets.append(f"{name}: recall {pct(s['recall'])} ({s['tp']} of {s['tp'] + s['fn']})")
        else:
            fpr = false_positive_rate(s["specificity"])
            variant_bullets.append(f"{name}: false-positive rate {pct(fpr)} ({s['fp']} of {s['fp'] + s['tn']})")
    slides.append(_slide(
        8, "Accuracy by variant type", variant_bullets,
        "Horizontal bars, one per variant type, or the variant table from report.pdf.",
        "Recall applies to positive variant types; false-positive rate applies to negative ones.",
    ))

    misses = [r for r in results if r.outcome == FN][:MAX_EXAMPLES]
    false_hits = [r for r in results if r.outcome == FP][:MAX_EXAMPLES]
    failure_bullets = [
        f"Missed: {r.query} -> expected {r.expected_match} (codes {_listed(sorted(encode(r.query)))} vs "
        f"{_listed(sorted(encode(r.expected_match or '')))})"
        for r in misses
    ]
    failure_bullets += [f"False match: {r.query} -> {_listed(r.candidates)}" for r in false_hits]
    if not failure_bullets:
        failure_bullets = ["No failures in this run"]
    slides.append(_slide(
        9, "Failure examples", failure_bullets,
        "Two-column table: misses on the left, false matches on the right.",
        f"{overall['fn']} misses and {overall['fp']} false matches in total. The full lists, with codes, "
        "are in report.pdf. A miss means the two names share no phonetic code.",
    ))

    slides.append(_slide(
        10, "Limitations",
        [
            "Ground truth was written by an LLM; 'sounds alike' is a judgement call",
            "Typos were excluded on purpose, so this says nothing about typo tolerance",
            "Only a few queries per length, so per-length rates are noisy",
            "Results depend on the size and density of the reference list",
        ],
        "Four short bullets, no chart.",
        "Treat the overall figures as the reliable result and the per-length chart as directional.",
    ))

    slides.append(_slide(
        11, "Recommendations", recommendations(summary),
        "Numbered list.",
        "These follow from the numbers above and the thresholds in slides.py. Suggestions that name a flag "
        "can be checked by re-running run_test.py with it.",
    ))

    path = Path(out_dir) / SLIDES_FILE
    header = (
        "# BMPM accuracy test: presentation content\n\n"
        "Generated from the same run as report.pdf. One section per slide; chart paths are relative to this file.\n"
    )
    path.write_text(header + "\n" + "\n".join(slides), encoding="utf-8")
    return path
