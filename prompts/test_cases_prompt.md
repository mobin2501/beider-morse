# Prompt: Generate the 200 test cases

## How to use
- Paste everything under **Prompt** into the LLM, and attach `data/names.csv` or
  paste its contents after the prompt.
- If the output gets cut off, ask for it in 4 batches: lengths 2–6, 7–11, 12–16
  and 17–21. Then concatenate the batches, keeping a single header row.
- Save the result as `data/test_cases.csv`.
- `run_test.py` validates the file: counts, lengths, targets, and the
  positive/negative split.

---

## Prompt

You are building labeled test cases for evaluating Beider-Morse Phonetic Matching
(BMPM), an algorithm that matches names by how they **sound**, not how they are
spelled. The attached file `names.csv` is the reference list of 1000 names that
queries are searched against.

Generate exactly **200 test cases** as CSV.

### Output format
- CSV with header:
  `case_id,query,length,case_type,expected_match,variant_type,rationale`
- `case_id`: `L<length two digits>-<index two digits>`, e.g. `L02-01` … `L21-10`
- `query`: the name searched for
- `length`: the number of characters in `query`, counting spaces and hyphens
- `case_type`: `positive` or `negative`
- `expected_match`: for a positive case, the **exact** name from `names.csv`
  (same spelling and case) that the query should match. Leave it **empty** for a
  negative case.
- `variant_type`: see below
- `rationale`: 20 words or fewer explaining why it should or should not match.
  Must not contain commas.
- Output **only** the CSV, with no commentary and no code fences.

### Distribution (strict)
- For **each query length from 2 to 21**: exactly 10 cases, of which **7 are
  positive and 3 are negative** (200 cases total: 140 positive, 60 negative).
- The *query's* length determines its bucket. The target name may differ in
  length by a few characters.
- Count every query's characters one by one before including it.

### Positive cases (should match `expected_match`)
The query must sound the same as, or nearly the same as, a name in the list
when spoken, but be spelled differently. Use one of these `variant_type` values:
- `spelling_variant`: an established alternative spelling
  (`Schmitt` → `Schmidt`, `Catherine` → `Kathryn`, `Philips` → `Phillips`)
- `transliteration`: a different romanization of the same name from a non-Latin
  script (`Muhammad` → `Mohammed`, `Tchaikovsky` → `Chaikovsky`, `Chang` → `Zhang`)
- `phonetic_respelling`: spelled the way it sounds, the way a listener might
  write it down (`Shmit` → `Schmidt`, `Filips` → `Phillips`)

Do **not** use keyboard typos, dropped letters or swapped letters that change the
sound (e.g. `Schmdit`). This test measures phonetic matching, not typo tolerance.

### Negative cases (should match nothing in the list)
The query must not sound like **any** name in `names.csv`. Use one of these
`variant_type` values:
- `look_alike`: visually similar to a list name but pronounced clearly
  differently (e.g. different consonants or vowels when spoken)
- `unrelated`: a real or plausible name with no phonetic counterpart in the list

### Rules
- `query` must **not** appear in `names.csv`, case-insensitively.
- Every `query` is unique across all 200 rows, case-insensitively.
- Every positive `expected_match` must appear in `names.csv` exactly as written.
- Use each list name as a target no more than once.
- Use plain ASCII letters only. Use spaces and hyphens only in compound names,
  and keep them consistent with the target's style.
- Write queries in Title Case.
- Spread origins and `variant_type` values across the set. Don't make every
  positive a `spelling_variant`.

### Self-check before answering
1. Each length 2..21 has exactly 7 positive and 3 negative rows.
2. The `length` column equals the true character count of `query`.
3. No `query` appears in `names.csv`, and no `query` repeats.
4. Every positive `expected_match` exists in `names.csv` verbatim, and every
   negative `expected_match` is empty.
5. There are exactly 200 data rows plus 1 header row.
