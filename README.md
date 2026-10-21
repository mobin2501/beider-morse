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

Place the name list in `data/names.csv` and the labeled test cases in
`data/test_cases.csv`.

The runner validates both files and aborts with a clear message if they don't
match the expected structure.

## Run

```bash
python run_test.py --names data/names.csv --cases data/test_cases.csv --out results/
```

Optional flags:
- `--name-mode {generic,ashkenazi,sephardic}` (default `generic`)
- `--match-mode {approx,exact}` (default `approx`)
- `--concat` — encode multi-word names as one word (default: per word, so
  "Garcia Rodriguez" matches "Rodriguez")
- `--allow-uneven` — report per-length count mismatches as warnings instead of errors

### Try it on the sample

`data/sample/` holds a small fixture (40 names, 24 cases) in the same format as
the real data. It doesn't have the full 50/10-per-length counts, so it needs
`--allow-uneven`:

```bash
python run_test.py --names data/sample/names.csv --cases data/sample/test_cases.csv \
  --out results/sample --allow-uneven
```

## Test

```bash
pytest
```
