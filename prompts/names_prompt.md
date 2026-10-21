# Prompt: Generate the 1000-name list

## How to use
- Paste everything under **Prompt** into the LLM.
- 1000 rows is long for one response. If the output gets cut off, ask for it in
  4 batches: lengths 2–6, 7–11, 12–16 and 17–21. Then concatenate the batches,
  keeping a single header row.
- Save the result as `data/names.csv`.
- LLMs often miscount characters. If the LLM can run code, ask it to check the
  lengths with code before answering. Either way, `run_test.py` validates the
  file and reports any wrong lengths.

---

## Prompt

You are building a test dataset for evaluating a phonetic name-matching algorithm
(Beider-Morse Phonetic Matching). Generate a list of exactly **1000 personal names**
as CSV.

### Output format
- CSV with header: `id,name,origin`
- `id`: integer 1..1000
- `name`: the name
- `origin`: one of `anglo`, `germanic`, `slavic`, `jewish`, `hispanic`, `italian`,
  `french`, `arabic`, `east_asian`, `south_asian`, `other`
- Output **only** the CSV, with no commentary and no code fences. Quote a field only
  if it contains a comma (none should).

### Length distribution (strict)
- **Length** = the number of characters in `name`, counting spaces and hyphens.
  Examples: `Li` = 2, `Schmidt` = 7, `Garcia-Lopez` = 12, `Van der Berg` = 12.
- Exactly **50 names for each length from 2 to 21** (20 lengths × 50 = 1000).
- Count every name's characters one by one before including it.

### Content rules
- Use plain ASCII letters A–Z/a–z. Do not use accents or apostrophes. Use spaces
  and hyphens only in compound names.
- Write names in Title Case (e.g. `Kowalski`, `Garcia-Lopez`).
- Names may be surnames, given names, or compound/double-barreled names. Use
  compound names (e.g. `Rodriguez-Hernandez`, `Bartholomew Fitzgerald`) mainly
  for lengths 15 and up, where single real names are rare.
- No duplicates, including case-insensitive duplicates.
- Every name must be real or highly plausible. No invented strings.
- Spread origins as evenly as each length allows. Short lengths will lean
  East Asian (`Li`, `Wu`, `Ng`, `Ho`); that's fine.
- Include names that have well-known spelling or transliteration variants
  (e.g. `Schmidt`, `Mohammed`, `Kowalski`, `Rabinowitz`, `Catherine`, `Zhang`).
  They will be used to write phonetic-variant test queries later.
- Do not put two spelling variants of the same name in the list (e.g. not both
  `Schmidt` and `Schmitt`). Each entry should be a distinct-sounding name.

### Self-check before answering
1. Each length 2..21 has exactly 50 rows.
2. The total is 1000 rows plus 1 header row.
3. There are no duplicates.
4. Every `origin` value comes from the allowed set.
