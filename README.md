# BMPM Accuracy Test

Measures the accuracy of Beider-Morse Phonetic Matching (via
[abydos](https://github.com/chrislit/abydos)) against a 1000-name list using
200 labeled queries — 10 per query length 2..21 (7 positive / 3 negative each).

Outputs: a terminal summary, `results/report.pdf`, and `results/presentation.md`
(slide content for building a deck).

## Setup

Requires Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data

Generate both CSVs with an LLM using the prompts in `prompts/`:

1. `prompts/names_prompt.md` → save output as `data/names.csv`
2. `prompts/test_cases_prompt.md` (attach `data/names.csv`) → save output as
   `data/test_cases.csv`

The runner validates both files and aborts with a clear message if they don't
match the expected structure.

## Run

```bash
python run_test.py --names data/names.csv --cases data/test_cases.csv --out results/
```

Optional flags: `--name-mode {generic,ashkenazi,sephardic}` (default `generic`),
`--match-mode {approx,exact}` (default `approx`).

## Test

```bash
pytest
```
