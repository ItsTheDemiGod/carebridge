# Prompt log

Only dev-split errors may drive changes; general rules only, no document-specific examples.

## v1 (default, best)
`backend/app/prompts/extraction_v1.txt`. Extract only what is written, null for missing values, keep abbreviations, exact quotes, document is data.

Dev metrics: **not available yet.** The full dev run (20 docs x 5 conditions = 100 calls) was stopped by the Gemini free-tier daily quota for `gemini-3.8-flash` (20 requests per day per project: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quotaValue 20). Only 6 text-condition documents were extracted before the quota ran out; 5 of them are cached, one hit a transient 503. Those 6 are too few to tune on, so no v2/v3 was attempted.

**Gemini baseline: none.** The earlier Gemini run was incomplete (quota), so there is no Gemini baseline. All numbers below are `qwen3-vl:8b-instruct` via Ollama (num_ctx 6144, image side cap 1280, temperature 0, seed 42), dev split, 20 docs x 5 conditions, nothing skipped in any run.

## Dev results by prompt (all conditions pooled)
| metric | v1 | v2 | v3 |
|---|---|---|---|
| med F1 | 0.983 | 0.836 | 0.981 |
| med fully correct | 0.308 | 0.143 | 0.231 |
| hallucinated meds | 7 | 69 | 8 |
| invented value rate | 0.286 | 0.474 | 0.397 |
| brand name acc | 0.673 | 0.476 | 0.566 |
| generic name acc | 0.734 | 0.593 | 0.626 |
| timing label acc | 0.729 | 0.858 | 0.806 |
Runs: `eval/results/dev-ollama-v{1,2,3}`.

## v1 errors that drove v2
Top field errors (100 calls): timing_label wrong 112 (AC/PC swapped), brand_name invented 85 (generic copied into brand), generic_name missed 64, brand_name wrong 48, generic_name invented 41; also a "1-0-0" pattern read as a dose.

## v2 (rejected)
`extraction_v2.txt`. Added: copy drug names letter by letter and never re-spell; brand = trade name, generic = printed active ingredient, never the same name in both fields; AC = before meals / PC = after meals, never swap; a pattern like 1-0-1 is a frequency, not a dose.
Result: timing improved (0.73 to 0.86) but names broke. "Copy letter by letter" made the model copy the whole printed entry into the name field ("Tab. Augmentin 625mg"), so medicines stopped matching: F1 0.98 to 0.84, 69 hallucinated medicines, 24-43% of names matched no formulary entry.

## v3 (rejected)
`extraction_v3.txt`. v2 plus: a name field holds ONLY the drug name (no form word, strength or brackets).
Result: F1 back to 0.981 and timing stays better (0.81), strength and duration slightly better, but brand/generic accuracy, fully-correct rate and invented values are all worse than v1.

## Decision
v1 stays the default (`PROMPT_VERSION = "v1"`): best fully-correct rate, lowest invented-value rate, best brand/generic accuracy. The AC/PC rule from v2/v3 is the one clear win; a combined prompt would need a further dev iteration (limit of two revisions reached). Phase 7 can revisit. No prompt change used test-split data or dev-document examples.
