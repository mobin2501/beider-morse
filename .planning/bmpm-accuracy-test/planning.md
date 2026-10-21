# BMPM Accuracy Test — Planning

## Goal
Measure the **accuracy** (not speed) of Beider-Morse Phonetic Matching (BMPM) on a
1000-name list using 200 labeled queries: 10 per query length 2..21
(7 positive / 3 negative each).

Outputs:
- Terminal summary
- `report.pdf`
- `presentation.md` — slide content; the user builds the deck themselves

## Premise challenges & mitigations
- **Weakest assumption: LLM-generated ground truth.** "Sounds alike" is subjective;
  labels reflect the LLM, not BMPM. Mitigation: each case carries a `variant_type` and a
  `rationale`; a validator enforces structure; the report breaks results down by variant
  type and lists every FN/FP for human review.
- **BMPM is phonetic, not typo-tolerant.** Keyboard typos are excluded from positives so
  the test measures what BMPM is designed for (stated in report limitations).
- **Length extremes are rare in real names** (2 and 19–21 chars). The name list is
  stratified: 50 names per length 2..21; long ones may be compound/double-barreled.
- **Verified:** abydos 0.5.0 runs on Python 3.12. Long names yield hundreds of codes
  (21 chars → 432), so expect more false positives at long lengths. Multi-word names
  encode per word, so a single-word overlap counts as a match.

## Key decisions
- **Environment:** Python's built-in `venv` (`python3 -m venv .venv`), dependencies
  pinned in `requirements.txt`. Isolates abydos' pinned deps from the global interpreter.
- **Library:** abydos `BeiderMorse`; defaults `name_mode=generic`, `match_mode=approx`,
  language auto-detect; overridable via CLI flags.
- **Match rule:** a query matches a list name if their BMPM code sets intersect
  (standard BMPM usage). An inverted index code → names is built once over the list.
- **Length** = `len(query)` including spaces and hyphens.
- **Case-level confusion matrix:**
  - TP = positive, target in matches
  - FN = positive, target missing
  - FP = negative, ≥1 match
  - TN = negative, no match
- **Metrics:** precision, recall, F1, accuracy, specificity; plus mean candidate-set
  size and candidate precision (mean of 1/|candidates| on hits) to expose over-matching.
- **Data:** CSVs the user generates with LLM prompts shipped in `prompts/`.
- **Report:** PDF via reportlab + matplotlib charts. `presentation.md` is generated from
  the same results so numbers never drift from the report.

## Architecture
```
run_test.py (CLI) -> bmpm_test/
  data.py     load + validate names/cases
  matcher.py  BMPM encode, index, match
  metrics.py  case outcomes + summaries (overall / by length / by variant)
  report.py   charts + report.pdf
  slides.py   presentation.md
prompts/  names_prompt.md, test_cases_prompt.md
data/     names.csv, test_cases.csv (+ tiny sample/ fixture)
results/  results.csv, summary.json, report.pdf, presentation.md, charts/
```

## Alternatives rejected
- **Apache commons-codec (Java):** canonical, but JVM setup with no benefit for an
  accuracy question.
- **Script-generated variants:** repeatable but unrealistic.
- **Including typos:** conflates spelling errors with phonetics.
- **Hand-written slides:** numbers drift from the report.
- **HTML → PDF (weasyprint):** extra system dependencies.
- **uv / conda for env:** user prefers the built-in `venv`.

## Tradeoffs accepted
- Ground-truth quality is bounded by the LLM; mitigated by transparency, not eliminated.
- abydos is unmaintained since 2020; pinned and verified on Python 3.12.
- n=10 per length → per-length rates are noisy (±~30%); the report states this and shows
  counts alongside percentages.
