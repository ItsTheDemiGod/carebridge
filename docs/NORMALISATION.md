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

# Phase 2i: hardening (re-scored from cached `dev-ollama-v1`, results in `eval/results/dev-ollama-v1-normalised-v2`)

## Strength mismatch (ground truth is right)
The ten cells with a model strength where ground truth is null are two prescriptions (rx_003, rx_012) x five conditions. In `data/generate_synthetic.py` (line ~245) a "messy" document drops the strength with 10% probability and sets the ground-truth strength to null at the same time, so text and label agree: the strength is not printed. The model filled the empty field with the dose ("1 cap", "2 puffs") or with another medicine's strength from a neighbouring line ("500 mg", "18 mcg"). No generator or ground-truth change was made (document text untouched).

## Quote checks (`backend/app/normalisation/quote_check.py`, evaluator and tests only)
The live app has no document text, so `normalise_document` takes the text only as an optional argument (it then adds `quote_not_in_document`); the service never depends on it.
- **normalised-exact**: Unicode NFKC, lowercase, all whitespace and line breaks collapsed, leading and trailing punctuation stripped.
- **strict-fuzzy**: best near-contiguous window of the document (window length varies by +-3 characters) with difflib ratio >= **0.95**, AND the window and the quote contain the same digits AND the same dosing abbreviations (OD, BD, TDS, QID, HS, AC, PC, SOS, PRN...).
- **Threshold choice** (420 dev medicine quotes): 375 are normalised-exact. The other 45 have ratios 0.83 to 0.99, with a clear mass at 0.96 to 0.99 (single misread characters such as `5D` read as `SD`, `MG/5 ML` as `MG/S ML`) and a thin tail at 0.83 to 0.95 (dropped or garbled tokens). Mutation tests on the exact quotes: at 0.95 a quote with one digit changed passes 0/375 (the digit gate does this at any threshold); a quote with another formulary drug name swapped in passes 9/351 (2.6%; 85/351 at the old 0.9 level, 2/351 at 0.97); 397 of 420 real quotes pass (399 at 0.9, 391 at 0.97). 0.95 keeps OCR-style noise and rejects the tail. The old 0.9 character-containment check was 1.0 everywhere; it is kept only as `quote_fuzzy_rate` for comparison.
- **Limit**: a dosing token dropped from the very END of a quote cannot be seen against the document, because the document legitimately continues after it. `incomplete_quote` (below) is the document-free safeguard.

Quote validity by condition (all item quotes, dev): exact 0.811, normalised-exact 0.916, strict 0.954 pooled (strict: text 0.975, clean 0.994, scan 0.950, photo 0.962, poor 0.887). 37 quotes fail strict: 13 with differing digits (for example `X B WEEKS`, `650mg` written `65mg`), 24 with low similarity (misread words or dropped tokens). Full table: `metrics.md`.

## `incomplete_quote` (model output only)
Raised when the quote cannot support values the model returned:
1. `strength`: a strength was returned but its characters (digits and unit) are not in the quote.
2. `dose`: a dose with a number was returned but that number is not a token in the quote.
3. `frequency`: times_per_day or is_prn was returned but the quote has no dosing abbreviation or phrase (a once-daily value supported by "at bedtime" or "at night" is accepted).
4. `timing`: the model returned a meal relation (before, after or with meals) and the quote shows no meal token (a different meal token is a conflict, not a gap); or it returned another specific time word or as_needed that the rules cannot find and which therefore survives into the final value.
5. `duration`: duration_days was returned but the quote has no duration token (days, weeks, fractions, months or years phrases, or the model's duration_text).
6. `too_short`: the quote is shorter than the printed name plus strength.
`reasons` names the parts (`incomplete_quote: strength,dose`).

**Revision (the one allowed for this rule).** The first version flagged `timing` whenever the model value had no supporting token, even when a rule had already replaced it with the quote-derived value. Before: 60 medicines carried the flag (precision 0.35) and 215 (51%) were at must_confirm. After (only meal-relation claims and surviving unsupported values count; "at bedtime" or "at night" supports once daily): 18 medicines carry it, 15 with a real remaining error (precision 0.83), and 194 (46%) are at must_confirm. No name error was unflagged before or after.

## Review levels
`review_level` is `must_confirm`, `note` or `none`; `needs_verification` is a computed alias (true when must_confirm). Any flag not explicitly in `NOTE_FLAGS` is must_confirm, so a new flag is safe by default.
- **must_confirm**: unresolved_name, near_miss_name (includes every fuzzy-accepted name), name_not_in_quote, role_corrected, duplicate_name_fields, missing_name, multiple_drugs_in_quote, possible_combination, incomplete_quote, conflicting_frequency, conflicting_meal_relation, conflicting_duration, ambiguous_OD, non_daily_frequency, unusual_strength, quote_not_in_document (only with document text), low model confidence.
- **note** (audit trail, no action): `conflict_times_per_day`, `conflict_timing_label`, `conflict_is_prn`, `conflict_duration_days`. The rule value is final and comes from the verbatim quote, and the incomplete_quote check guards against a truncated quote. Evidence: treating them as must_confirm raises the share from 46% to 65% and catches no additional error (timing unflagged stays 1).
- `role_corrected` was audit-only in Phase 2h. The Phase 2i breakdown showed it on a real remaining name error (a brand lost from the model's fields and quote), and it is name-related, so it is now must_confirm.

## Flag breakdown (pooled, dev, after revision)
| flag | medicines | with any remaining error | precision |
|---|---|---|---|
| conflict_timing_label (note) | 109 | 23 | 0.21 |
| role_corrected | 61 | 10 | 0.16 |
| duplicate_name_fields | 59 | 14 | 0.24 |
| near_miss_name | 38 | 19 | 0.50 |
| name_not_in_quote | 19 | 2 | 0.11 |
| conflict_duration_days (note) | 18 | 4 | 0.22 |
| incomplete_quote | 18 | 15 | 0.83 |
| unusual_strength | 16 | 16 | 1.00 |
| non_daily_frequency | 15 | 15 | 1.00 |
| conflict_times_per_day (note) | 13 | 7 | 0.54 |
| unresolved_name | 8 | 8 | 1.00 |

Name-related flags have low precision because only 14 of 420 medicines have a wrong name left; they fire on correct medicines as warnings about the model's input. No name, strength, frequency or duration flag was downgraded to improve a number.

## Review-level results (app mode, dev, 420 medicines)
| | Phase 2h | Phase 2i |
|---|---|---|
| medicines needing confirmation | 133 (32%) | 194 (46%) |
| name errors left / unflagged | 14 / 1 | 14 / 0 |
| name flag precision / recall | 0.098 / 0.929 | 0.072 / 1.0 |
| timing errors left / unflagged | 4 / 1 | 4 / 1 |
| timing precision / recall | 0.023 / 0.75 | 0.015 / 0.75 |

The load is higher than Phase 2h by design: promoting role_corrected and adding incomplete_quote bought full name recall. Per condition the share is 30% (text), 39% (clean), 50% (scan), 54% (photo) and 58% (poor). The remaining unflagged timing error is a truncated quote whose lost token the model never reported ("AC" dropped, model said unspecified); only the document-text check sees it. With document text, unflagged name and timing errors are both 0.

## Readiness fields
- `resolved_generic` comes ONLY from the formulary via a name PRINTED in the quote (exact, or fuzzy at >= 0.92 with a 0.05 margin over any other drug). The model's own `generic_name` is never used to resolve (audited: `resolve_names` takes `hits` from the quote scan only; the model's names are compared with the quote and kept as `as_written_*`). A garbled or unknown printed name gives `resolved_generic = None`; a garbled combination containing "+" is refused (`possible_combination`).
- `interaction_ready` = `resolved_generic` set from an EXACT printed-name match AND review_level is not must_confirm. A fuzzy-accepted name carries `resolved_generic` for display but is never interaction_ready.
- `schedule_ready` = review_level is not must_confirm AND not PRN AND no `non_daily_frequency` AND times_per_day known AND timing_label known and not `as_needed` or `other` (`unspecified` counts as known: no time of day was written). Weekly and other non-daily medicines are never schedule_ready.
- **Rule for later phases**: Phase 4 checks interactions only for interaction_ready medicines and reports every other medicine as "not checked"; Phase 6 builds reminders only for schedule_ready medicines and asks the user to confirm the rest.
- Dev counts: interaction_ready 226 of 420 (text 59, clean 51, scan 42, photo 39, poor 35), schedule_ready 180 (48, 39, 35, 30, 28). Against ground truth: 0 interaction_ready medicines with a wrong resolved_generic; 1 schedule_ready medicine with a wrong timing label (the truncated-quote case).

## Limits (additions)
- Name-resolution scores on synthetic data are an optimistic UPPER BOUND: the generator and the resolver share the same 66-drug formulary.
- Combination products resolve to a "+"-joined generic; Phase 4 must split components before looking up interactions.
- Readiness numbers come from one local model run (prompt v1) on 20 dev documents.
