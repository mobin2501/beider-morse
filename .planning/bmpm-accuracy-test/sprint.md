# BMPM Accuracy Test — Sprint

## T1 Scaffold — PENDING
- Create virtual env with built-in venv: `python3 -m venv .venv`
- `requirements.txt` with pinned abydos, reportlab, matplotlib, pytest
- `.gitignore` (`.venv/`, `__pycache__/`, `results/`)
- README: setup (venv + pip install) and run instructions
- Package skeleton `bmpm_test/`

## T2 LLM prompts — PENDING
- `prompts/names_prompt.md` → CSV `id,name,origin`
  - Exactly 50 unique names per length 2..21 (1000 total)
  - Mixed origins: Anglo, Germanic, Slavic, Jewish, Hispanic, Italian, Arabic,
    East/South Asian, etc.
- `prompts/test_cases_prompt.md` → CSV
  `case_id,query,length,case_type,expected_match,variant_type,rationale`
  - 10 per length, 7 positive / 3 negative
  - Positive `variant_type` ∈ {spelling_variant, transliteration, phonetic_respelling}
  - Negative `variant_type` ∈ {look_alike, unrelated}
  - `expected_match` = exact list name (positive) or empty (negative)
  - Query must not itself be in the list

## T3 Data + validation — PENDING
- `load_names`, `load_cases`
- `validate_names`: count, duplicates, length stratification
- `validate_cases`: 10/length, 7/3 split, `length == len(query)`, targets exist,
  negatives have empty target
- Clear error messages; abort on failure

## T4 Matcher — PENDING
- `BMPMMatcher(name_mode, match_mode)`
  - `encode()` → `set[str]`
  - `build_index(names)` — inverted index code → names
  - `match(query)` → `list[str]`

## T5 Metrics — PENDING
- `evaluate_cases` → per-case outcome rows (TP/FN/FP/TN, candidates)
- `summarize_overall`, `summarize_by_length`, `summarize_by_variant`

## T6 CLI — PENDING
- `run_test.py --names --cases --out --name-mode --match-mode`
- Prints config, overall metrics, per-length table
- Writes `results.csv` + `summary.json`

## T7 PDF report — PENDING
- `build_report`: title/config, dataset summary, overall metrics, confusion matrix,
  recall & FPR by length chart, candidate-set size by length chart, by-variant table,
  all FN/FP listed, methodology + limitations
- Load dataviz skill before writing chart code

## T8 presentation.md — PENDING
- `build_slides`: ~10 slides — title, goal, method, dataset, headline metrics, by length,
  over-matching, failure examples, limitations, recommendations
- Include chart paths + speaker notes

## T9 Tests + E2E — PENDING
- pytest for validation and metrics
- Sample fixture in `data/sample/`
- E2E run on sample, then on user data when provided
