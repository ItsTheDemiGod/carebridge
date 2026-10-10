# Normalisation layer (Phase 2h)

Deterministic, rule-based post-processing of the model's medication output. No model calls. Code: `backend/app/normalisation/{abbreviations,names}.py`, `backend/app/services/normalisation.py`, schema `backend/app/schemas/normalised.py`, re-scoring `eval/rescore.py`.

## Decision rule
- Where the abbreviation table derives a value from the verbatim `source_quote`, the **rule value is final**. If the model said something different, provenance is `conflict`, both values are kept (`model_value`, `rule_value`) and a `conflict_<field>` flag is recorded.
- Where the rules derive nothing, the **model's value is kept** (provenance `model`).
- Names are **never silently corrected**. The model's text is kept as `as_written_*`; what the document prints (formulary spelling) is `printed_*`; the formulary's generic for the printed drug is `resolved_generic` (provenance `formulary`), kept apart from `printed_generic` because a document may print only the brand.
- A final name must be printed in the quote (or be an unknown name that is in the quote, flagged). Role comes from the formulary: a generic is never placed in the brand field.

## Abbreviation rules (`abbreviations.py`)
Whole tokens only, case-insensitive, dots tolerated (`b.d.`, `T.D.S.`). Written from standard prescription shorthand, not from dev documents.
- Frequency: OD/QD 1, BD/BID 2, TDS/TID 3, QID/QDS 4, HS 1 (bedtime); "once / twice / thrice / N times a day|daily", "daily"; "every N hours" and qNh (only when 24 divides by N); hyphen patterns `1-0-1` (count of non-zero slots).
- Timing precedence: meal relation (AC before, PC after, "with meals/food", "before/after food|meals") > exactly one time word (morning, afternoon, evening, night, bedtime, HS) > as_needed (SOS, PRN, "as needed") > `unspecified` when a frequency is known > nothing. A single-slot pattern means morning (1-0-0), afternoon (0-1-0) or night (0-0-1).
- PRN entries keep `times_per_day` null (schema convention).
- Duration: `x 5 days`, `5d`, `for 3d`, `x 5/7` (days), `x 2/52` (weeks), `2 weeks`/`wk`.
- Ambiguity flags, nothing derived: `ambiguous_OD` (OD for drops or when the entry mentions eye/ocular/ophthalmic), `conflicting_frequency`, `conflicting_meal_relation`, `conflicting_duration`.

## Name resolution (`names.py`)
Scan the quote for formulary names: exact n-gram matches (up to 5 tokens, longest first), then guarded fuzzy matches on remaining single words.
- **Thresholds, chosen from the formulary itself**: the formulary has 189 distinct names and no name shared between drugs. The most similar pairs of names of different drugs (difflib ratio): omeprazole / esomeprazole 0.91, dapagliflozin / empagliflozin 0.85, cetirizine / levocetirizine 0.83, losar / olsar 0.80, then sitagliptin / vildagliptin, losartan / olmesartan, cefixime / cefuroxime 0.78. Therefore `FUZZY_MIN = 0.92` (above the highest confusable pair, so a fuzzy match cannot reach another drug's name), `MARGIN = 0.05` over the best other drug, words shorter than 5 letters must match exactly. `NEAR_MIN = 0.75` is used only to report a near miss, never to accept.
- Tested: every formulary name resolves to itself and nothing else; every one-letter drop/substitution/swap of every name either resolves to the same drug or to nothing.
- A fuzzy match is accepted (formulary spelling in `printed_*`) but always flagged `near_miss_name`. A closest-name hint without acceptance is also `near_miss_name` plus `unresolved_name`.
- A "+" in the entry with no matched combination name (a garbled combination would match one component only) is refused: `possible_combination`. Two different drugs in one entry: `multiple_drugs_in_quote`.

## Flags
| flag | meaning |
|---|---|
| `unresolved_name` | no formulary name found in the quote; names kept as written, no drug forced |
| `near_miss_name` | a name is close to, but not exactly, a formulary name (fuzzy-accepted or only suggested); see `near_miss_name` field |
| `name_not_in_quote` | a name the model returned is not in its own quote |
| `role_corrected` | the model put a generic in the brand field (or reverse); audit-only |
| `duplicate_name_fields` | the model wrote the same name in both fields; the other printed name was probably lost |
| `non_daily_frequency` | weekly / monthly / alternate-day wording: `times_per_day` cannot express it, nothing derived |
| `missing_name` | no usable name at all |
| `multiple_drugs_in_quote`, `possible_combination` | see above |
| `unusual_strength` | strength is not one of the formulary strengths for the resolved drug (not changed) |
| `conflict_times_per_day`, `conflict_timing_label`, `conflict_is_prn`, `conflict_duration_days` | model and rule disagreed; the rule value is final |
| `ambiguous_OD`, `conflicting_*` | rules refused to derive a value |
| low confidence | model said `low`; added to `reasons` |

`needs_verification` is true if any flag except the audit-only ones (`conflict_*`, `role_corrected`) is raised, or the model's confidence is low; `reasons` lists them. All flags stay in `flags` (audit trail). Before the revision below, every flag raised it.

## Results (dev, prompt v1, cached outputs of `dev-ollama-v1`)
See `eval/results/dev-ollama-v1-normalised/metrics.md` (raw and normalised side by side, flag effectiveness).

## The one revision (Step 6), general rules only
Evidence from the first pass: 255 of 420 medicines needed verification (61%) and flag precision was 0.055 for names, because `conflict_*` and `role_corrected` mostly describe cases the rules had already fixed. Changes: (1) those flags became audit-only; new `duplicate_name_fields` (verify) separates "same name in both fields" from a plain role swap; (2) `non_daily_frequency` rule (weekly etc. derive nothing and flag); (3) an unknown model-written brand that is in the quote is kept even when a generic is printed (strength and form words are stripped before the formulary check; a first version of that strip also dropped tokens like `D3` and kept a formulary generic as a brand: fixed, tested).

| dev, all conditions | before | after |
|---|---|---|
| medicines needing verification | 255 / 420 | 133 / 420 |
| name errors remaining / unflagged (needs_verification) | 14 / 0 | 14 / 1 |
| name flag precision (needs_verification) | 0.055 | 0.098 |
| name flag recall | 1.0 | 0.929 |
| timing errors remaining / unflagged | 4 / 2 | 4 / 1 |
| timing flag recall / precision | 0.5 / 0.008 | 0.75 / 0.023 |
| brand accuracy | 0.976 | 0.979 |
| invented-value rate | 0.060 | 0.056 |

The trade is explicit: precision doubled and the flagged load halved, at the cost of one remaining unflagged name error (a brand missing from both the model's fields and its quote, shown as null, not a wrong name). Flag precision is still low because most flags (near-miss, duplicate name fields) fire on medicines whose final values are correct; they are warnings about the model's input, not about the output.

## Limits
- The formulary has **66 drugs**. Real-world names outside it are `unresolved_name` and flagged, never forced.
- The synthetic documents use **only formulary names**, so name-resolution scores here are optimistic and must not be presented as real-world accuracy. Role correction and timing rules are the parts expected to transfer.
- Rules read the model's `source_quote`. If the model truncates its quote (drops "AC"), the rule cannot see the text; this produced the remaining unflagged timing errors.
- `unspecified` is derived when a frequency is known and no meal/time word is in the quote; it is only as good as the quote.
- Hyphen patterns are assumed morning-noon-night; other conventions are not handled.
