"""Render report.pdf from the run summary and per-case results."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from bmpm_test.charts import (
    AXIS,
    GRID,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    build_charts,
    false_positive_rate,
)
from bmpm_test.metrics import FN, FP, CaseResult

REPORT_FILE = "report.pdf"
CHARTS_DIR = "charts"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

MAX_LISTED = 4  # candidates / codes shown per failure row before "+N more"

_base = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle("title", parent=_base["Title"], alignment=TA_LEFT, fontSize=20,
                            leading=24, textColor=colors.HexColor(TEXT_PRIMARY), spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Normal"], fontSize=9, leading=12,
                               textColor=colors.HexColor(TEXT_SECONDARY)),
    "h2": ParagraphStyle("h2", parent=_base["Heading2"], fontSize=13, leading=16,
                         textColor=colors.HexColor(TEXT_PRIMARY), spaceBefore=12, spaceAfter=6),
    "body": ParagraphStyle("body", parent=_base["Normal"], fontSize=9.5, leading=13.5,
                           textColor=colors.HexColor(TEXT_PRIMARY), spaceAfter=6),
    "bullet": ParagraphStyle("bullet", parent=_base["Normal"], fontSize=9.5, leading=13.5,
                             leftIndent=10, bulletIndent=0, textColor=colors.HexColor(TEXT_PRIMARY)),
    "cell": ParagraphStyle("cell", parent=_base["Normal"], fontSize=7.5, leading=9.5,
                           textColor=colors.HexColor(TEXT_PRIMARY)),
    "tile_label": ParagraphStyle("tile_label", parent=_base["Normal"], fontSize=8, leading=10,
                                 textColor=colors.HexColor(TEXT_SECONDARY)),
    "tile_value": ParagraphStyle("tile_value", parent=_base["Normal"], fontName="Helvetica-Bold",
                                 fontSize=18, leading=22, textColor=colors.HexColor(TEXT_PRIMARY)),
}

TABLE_STYLE = TableStyle([
    ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(TEXT_PRIMARY)),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(TEXT_SECONDARY)),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(AXIS)),
    ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(GRID)),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
])


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _listed(items, limit: int = MAX_LISTED) -> str:
    items = list(items)
    if not items:
        return "(none)"
    shown = ", ".join(items[:limit])
    return shown if len(items) <= limit else f"{shown} +{len(items) - limit} more"


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def _bullet(text: str) -> Paragraph:
    return Paragraph(text, STYLES["bullet"], bulletText="\u2022")


def _cell(text: str) -> Paragraph:
    return Paragraph(escape(text), STYLES["cell"])


def _table(rows: list[list], col_widths: list[float], left_align_cols: int = 1) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    style = TableStyle(TABLE_STYLE.getCommands())
    style.add("ALIGN", (0, 0), (left_align_cols - 1, -1), "LEFT")
    table.setStyle(style)
    return table


# --- sections ----------------------------------------------------------------

def html_bold(text: str) -> str:
    return f"<b>{text}</b>"


def takeaway(summary: dict, bold: Callable[[str], str] = html_bold) -> str:
    """Plain-English headline; ``bold`` lets markdown callers swap the emphasis markup."""
    o = summary["overall"]
    positives, negatives = o["tp"] + o["fn"], o["fp"] + o["tn"]
    parts = []
    if positives:
        found = bold(f"{o['tp']} of {positives}")
        parts.append(f"BMPM found the intended name for {found} positive queries (recall {pct(o['recall'])}).")
    if negatives:
        matched = bold(f"{o['fp']} of {negatives}")
        parts.append(f"{matched} negative queries matched at least one name "
                     f"(false-positive rate {pct(false_positive_rate(o['specificity']))}).")
    parts.append(f"Each query returned {num(o['mean_candidates'])} names on average.")

    by_length = summary["by_length"]
    scored = [(s["recall"], int(k)) for k, s in by_length.items() if s["recall"] is not None]
    if scored:
        worst_recall, worst_len = min(scored)
        parts.append(f"Recall was lowest at length {worst_len} ({pct(worst_recall)}).")
    fprs = [(false_positive_rate(s["specificity"]), int(k)) for k, s in by_length.items()
            if s["specificity"] is not None]
    if fprs:
        worst_fpr, fpr_len = max(fprs)
        if worst_fpr > 0:
            parts.append(f"False positives peaked at length {fpr_len} ({pct(worst_fpr)}).")
    return " ".join(parts)


def _kpi_tiles(overall: dict) -> Table:
    tiles = [
        ("Recall", overall["recall"]),
        ("Precision", overall["precision"]),
        ("F1", overall["f1"]),
        ("Specificity", overall["specificity"]),
        ("Accuracy", overall["accuracy"]),
    ]
    row = [[_p(label, "tile_label"), _p(pct(value), "tile_value")] for label, value in tiles]
    table = Table([row], colWidths=[CONTENT_WIDTH / len(tiles)] * len(tiles), hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(GRID)),
        ("LINEAFTER", (0, 0), (-2, -1), 0.6, colors.HexColor(GRID)),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _dataset_section(summary: dict, results: list[CaseResult]) -> list:
    d = summary["dataset"]
    variants = Counter((r.case_type, r.variant_type) for r in results)
    rows = [["Case type", "Variant type", "Cases"]]
    rows += [[ct, vt, str(n)] for (ct, vt), n in sorted(variants.items())]
    lengths = sorted(summary["by_length"], key=int)
    span = f"{lengths[0]}-{lengths[-1]}" if lengths else "n/a"
    return [
        _p("Dataset", "h2"),
        _p(f"{d['names']} reference names; {d['cases']} test queries ({d['positives']} positive, "
           f"{d['negatives']} negative) across query lengths {span}."),
        _table(rows, [40 * mm, 50 * mm, 20 * mm], left_align_cols=2),
    ]


def _confusion_section(overall: dict) -> list:
    rows = [
        ["", "Matched", "Not matched"],
        ["Positive (should match)", f"TP {overall['tp']}", f"FN {overall['fn']}"],
        ["Negative (should not match)", f"FP {overall['fp']}", f"TN {overall['tn']}"],
    ]
    return [
        _p("Confusion matrix", "h2"),
        _p("A positive counts as matched only if its <i>intended</i> name is among the results. "
           "A negative counts as matched if <i>any</i> name is returned."),
        _table(rows, [55 * mm, 30 * mm, 30 * mm]),
    ]


def _summary_rows(label_header: str, groups: dict) -> list[list[str]]:
    rows = [[label_header, "N", "TP", "FN", "FP", "TN", "Recall", "FPR", "Precision", "F1", "Avg names"]]
    for label, s in groups.items():
        rows.append([
            str(label), str(s["n"]), str(s["tp"]), str(s["fn"]), str(s["fp"]), str(s["tn"]),
            pct(s["recall"]), pct(false_positive_rate(s["specificity"])), pct(s["precision"]),
            pct(s["f1"]), num(s["mean_candidates"]),
        ])
    return rows


SUMMARY_COL_WIDTHS = [30 * mm] + [11 * mm] * 5 + [17 * mm] * 3 + [14 * mm, 21 * mm]


def _chart(path: Path) -> Image:
    width = CONTENT_WIDTH
    return Image(str(path), width=width, height=width * 3.2 / 7.0)


def noise_note(summary: dict) -> str:
    """Explain how much one case moves a per-length rate, from the actual bucket sizes."""
    splits = {(s["tp"] + s["fn"], s["fp"] + s["tn"]) for s in summary["by_length"].values()}
    if len(splits) == 1:
        positives, negatives = splits.pop()
        if positives and negatives:
            return (f"Each length has {positives + negatives} queries ({positives} positive, {negatives} negative), "
                    f"so a single case moves recall by ~{100 / positives:.0f} points and the false-positive "
                    f"rate by ~{100 / negatives:.0f} points. Read the trend, not individual points.")
    sizes = [s["n"] for s in summary["by_length"].values()]
    return (f"Lengths have between {min(sizes, default=0)} and {max(sizes, default=0)} queries, so per-length "
            "rates are noisy. Read the trend, not individual points.")


def _length_section(summary: dict, chart: Path) -> list:
    return [
        _p("Accuracy by query length", "h2"),
        _p(noise_note(summary)),
        _chart(chart),
        Spacer(1, 4),
        _table(_summary_rows("Length", summary["by_length"]), SUMMARY_COL_WIDTHS),
    ]


def _overmatch_section(summary: dict, chart: Path) -> list:
    o = summary["overall"]
    return [
        _p("Over-matching", "h2"),
        _p(f"BMPM returns every list name that shares a phonetic code with the query. Across all queries "
           f"it returned {num(o['mean_candidates'])} names on average. When the intended name was found, "
           f"it made up {pct(o['candidate_precision'])} of the returned names on average "
           f"(candidate precision; 100% means it was the only match)."),
        _chart(chart),
    ]


def _variant_section(summary: dict) -> list:
    return [
        _p("Accuracy by variant type", "h2"),
        _p("Recall applies to positive variant types; FPR applies to negative ones (look-alike and unrelated)."),
        _table(_summary_rows("Variant", summary["by_variant"]), SUMMARY_COL_WIDTHS),
    ]


def _failure_section(results: list[CaseResult], encode: Callable[[str], frozenset[str]]) -> list:
    misses = [r for r in results if r.outcome == FN]
    false_hits = [r for r in results if r.outcome == FP]
    out = [_p("Failures", "h2")]

    out.append(_p(f"<b>False negatives ({len(misses)})</b>: the intended name was not returned. "
                  "Codes show why: a match needs at least one shared code."))
    if misses:
        rows = [["Case", "Query", "Expected", "Returned instead", "Query codes", "Expected codes"]]
        for r in misses:
            rows.append([
                _cell(r.case_id), _cell(r.query), _cell(r.expected_match or ""),
                _cell(_listed(r.candidates)),
                _cell(_listed(sorted(encode(r.query)))),
                _cell(_listed(sorted(encode(r.expected_match or "")))),
            ])
        out.append(_table(rows, [15 * mm, 27 * mm, 27 * mm, 34 * mm, 35 * mm, 35 * mm], left_align_cols=6))
    out.append(Spacer(1, 8))

    out.append(_p(f"<b>False positives ({len(false_hits)})</b>: a query that should match nothing "
                  "returned one or more names."))
    if false_hits:
        rows = [["Case", "Query", "Variant", "Names returned", "Count"]]
        for r in false_hits:
            rows.append([
                _cell(r.case_id), _cell(r.query), _cell(r.variant_type),
                _cell(_listed(r.candidates, limit=8)), str(len(r.candidates)),
            ])
        out.append(_table(rows, [15 * mm, 35 * mm, 25 * mm, 85 * mm, 14 * mm], left_align_cols=4))
    return out


def _method_section(summary: dict) -> list:
    config = summary["config"]
    word_mode = (
        "Multi-word and hyphenated names were encoded as a single word (<i>concat</i> on), so compound "
        "names only match whole compounds."
        if config["concat"] else
        "Multi-word and hyphenated names were encoded per word (the library default), so a query matches "
        "a list name when any single word sounds alike, e.g. 'Garcia Rodriguez' matches 'Rodriguez'."
    )
    bullets = [
        f"Implementation: abydos {escape(config['abydos_version'])} BeiderMorse, name mode "
        f"<i>{config['name_mode']}</i>, match mode <i>{config['match_mode']}</i>, language auto-detected.",
        "Match rule: a query matches a list name when their sets of BMPM phonetic codes share at least "
        "one code. Each query is compared against all reference names.",
        word_mode,
        "Outcomes are counted per case. Extra names returned on a positive case are not false positives; "
        "they are reported as over-matching instead.",
    ]
    limitations = [
        "Ground truth was written by an LLM. Whether two names 'sound alike' is a judgement call, so "
        "some failures may be labeling errors. Every failure is listed above for review.",
        "Keyboard typos were deliberately excluded. BMPM matches by sound, so these results do not "
        "describe typo tolerance.",
        "Per-length rates rest on a handful of queries each and are noisy. Overall figures "
        f"({summary['dataset']['cases']} queries) are more reliable.",
        "Results depend on the reference list: a larger or denser list raises the chance that a "
        "negative query shares a code with some name.",
    ]
    return [
        _p("Methodology", "h2"),
        *[_bullet(b) for b in bullets],
        _p("Limitations", "h2"),
        *[_bullet(b) for b in limitations],
    ]


def _warnings_section(warnings: list[str]) -> list:
    if not warnings:
        return []
    return [
        _p("Appendix: validation warnings", "h2"),
        *[_bullet(escape(w)) for w in warnings],
    ]


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor(TEXT_MUTED))
    canvas.drawString(MARGIN, 10 * mm, "BMPM accuracy report")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_report(
    out_dir: Path,
    summary: dict,
    results: list[CaseResult],
    encode: Callable[[str], frozenset[str]],
) -> Path:
    """Write charts and report.pdf into ``out_dir``; return the PDF path."""
    out_dir = Path(out_dir)
    charts = build_charts(summary, out_dir / CHARTS_DIR)
    config = summary["config"]
    word_mode = "concat" if config["concat"] else "per-word"

    story = [
        _p("Beider-Morse Phonetic Matching: accuracy report", "title"),
        _p(f"Run {escape(config['run_at'])} &middot; name mode {config['name_mode']} &middot; "
           f"match mode {config['match_mode']} &middot; {word_mode} encoding", "subtitle"),
        Spacer(1, 10),
        _p("Summary", "h2"),
        _kpi_tiles(summary["overall"]),
        Spacer(1, 8),
        _p(takeaway(summary)),
        *_dataset_section(summary, results),
        KeepTogether(_confusion_section(summary["overall"])),
        PageBreak(),
        *_length_section(summary, charts["recall_fpr"]),
        PageBreak(),
        *_overmatch_section(summary, charts["candidates"]),
        *_variant_section(summary),
        PageBreak(),
        *_failure_section(results, encode),
        PageBreak(),
        *_method_section(summary),
        *_warnings_section(summary["warnings"]),
    ]

    path = out_dir / REPORT_FILE
    doc = SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 4 * mm,
        title="BMPM accuracy report", author="bmpm_test",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path
