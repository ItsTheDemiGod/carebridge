**POST-HOC (descriptive, done after the official run; not an official result; nothing in the system was changed in response).**

# Case review of the official final test (final-test-v1)

Sources (all read-only): the cached raw model outputs `eval/runs/final-test-v1/raw`, the explanation records `eval/runs/final-test-v1/docs`, the test ground truth and the manifest, run through the frozen code (`scripts/posthoc_peek.py`, `scripts/posthoc_silent.py`, `scripts/posthoc_explore.py`, `scripts/posthoc_analyse.py`). No model was called. Excerpts are field-level only. "App mode" = the normaliser sees the model output only, never the document text (so the strict quote check, which needs the text, cannot run in the app). The cases reproduce the official counts exactly (2 wrong schedules, 3 strict silent misses, 1 unflagged name error, 1 normalised hallucinated medicine).

## (a) The 2 wrong schedules among the 285 schedule_ready medicines (both `scan`)

Counted as wrong by the evaluator when times_per_day, timing_label or is_prn differs from ground truth for a medicine that is `schedule_ready`.

| | ds_035 (copd, abbreviated), scan | ds_038 (cap, abbreviated), scan |
|---|---|---|
| medicine | Ventolin inhaler 100 mcg, 2 puffs | Augmentin 625 mg, 1 tablet |
| what the document says | `... 2 puffs SOS` (as needed) | `... 1 tab BD PC x 5 days` (twice daily, after meals) |
| what the model returned (quote) | `... 2 puffs OD` (once daily) | `... 1 tab BD x 5 days` (the token `PC` is missing); its timing label was "afternoon" |
| what the system derived | 1 per day, timing unspecified, is_prn false | 2 per day (right), timing unspecified (should be after meals) |
| why it went wrong | the model misread SOS as OD in the scan image; the quote is consistent with the misreading, so nothing disagrees | the model's quote dropped a dosing token (PC); the rule table can only use the quote it is given |
| flag shown | none (review level none) | `conflict_timing_label` (model said afternoon, rule said unspecified; rule value kept); level "note", not "must confirm" |
| other conditions | the quote kept SOS in text, clean and photo (all three were not schedule_ready: must confirm or as-needed); in poor the same OD misreading occurred but the card carried `duplicate_name_fields` (must confirm), so it was not schedule_ready | the quote kept PC in text, clean, photo and poor (text and poor carried the same conflict note, photo was must confirm); it lost it only in scan |

What the schedule page shows (from `services/schedule.py`): for ds_035 a daily reminder suggestion at 08:00 for an as-needed inhaler, with the standing notice "Suggested times only; adjust them..." and "No meal timing was found in the document..."; no confirmation banner. For ds_038 two suggested times, 08:00 and 22:00 (spread through the day, not the after-meal slots), the same two notices, and the card carries a "Note" marker. In both cases the user can compare with the photo pane beside the card, but nothing prompts them to.

User-visible outcome: a daily reminder time for an as-needed inhaler (ds_035) with no warning at all, and spread-out dose times instead of after-meal times for Augmentin (ds_038) with only a "Note" marker.

## (b) The 3 strict silent misses

All three are in ONE document and condition: ds_028 (t2dm_htn, clean), `photo`. Ground-truth pairs: 3 pairs involving the first medicine (Metformin) with each of the other three medicines of the document; levels: 1 moderate, 2 unknown.

- Extraction for the relevant row: the photo reading returned the first medicine as "Performin" (generic field "Glimipride", copied from the next row), 500 mg, with the correct dose line. The evaluator could not pair this row with the ground-truth Metformin row, so the three pairs had "no entry" (hence "strict").
- Flag-covered state: yes, for all 3. The row carries `unresolved_name`, `near_miss_name`, `name_not_in_quote` (review level must_confirm), is not interaction_ready, so the engine cannot report a found interaction for it and reports its pairs as `not_checked_unconfirmed`. The evaluator's own covered-by-flag test is true for each of the 3, so the count "not covered by a flag" stays 0.
- This is the same row as case (d).

User-visible outcome: the Performin card asks the user to confirm the medicine, and its pairs are counted under "we could not check these until the name is confirmed"; no interaction is shown and none is called safe.

## (c) The 1 unflagged name error (condition `text`)

ds_024 (gastro, messy), `text`, the first medicine. Ground truth: generic racecadotril, no brand, 100 mg, 1 capsule, tds before meals, 3 days. The model put the whole line in the brand field (`cap. racecadotril 100 mg`) and left the generic empty. The normaliser stripped the form prefix and strength, matched the formulary generic exactly (Racecadotril, provenance formulary) and kept the model's text as the brand field. No flag fired because the identity resolved exactly and every other field (strength, 3 per day, before meals, 3 days) is right; the evaluator counts it as a name error only because the brand field differs from ground truth (empty). The resolved identity is correct, the schedule is correct, and it is interaction_ready and schedule_ready correctly. I did not render the page; from the record, the card carries the right medicine with the line text in the brand slot.

User-visible outcome: the right medicine with correct times, but the brand slot shows the whole printed line ("cap. racecadotril 100 mg") instead of nothing; no flag and no wrong identity.

## (d) The 1 remaining hallucinated medicine after rules

ds_028 (t2dm_htn, clean), `photo`: the row "Performin" (generic "Glimipride"), strength 500 mg, dose line `1 tablet twice daily after meals`. It is not an invented drug: its dose line and strength match the ground-truth Metformin row, which therefore counts as missed (one false positive, one false negative). Flags: `unresolved_name`, `near_miss_name`, `name_not_in_quote`; review level must_confirm; interaction_ready false, schedule_ready false.

User-visible outcome: a must-confirm card for an unrecognised name that cannot be scheduled or checked until the user picks the medicine from the list (the picker is never pre-filled).

## (e) The 2 explanation calls that failed with `context_truncated`

Both are Tamil translation calls (stage translate, lang ta) on the `clean` reading; Hindi and English were not affected.

| document | calls | lines whose Tamil text was lost to the failure | other lines |
|---|---|---|---|
| ds_024 (gastro, messy) | 4 model requests, last error context_truncated | follow_up-0, advice-0, advice-1, advice-2 (4 lines) | advice-3 matched the phrase library (no model); warning-0..2 translated but failed the judge (contradicts, contradicts, omits) |
| rx_019 (copd, clean) | 5 model requests, last error context_truncated | follow_up-0, advice-0, advice-1, warning-0 (4 lines) | warning-1 translated but failed the judge (contradicts) |

Confirmed from the cached records and from `services/explain.py` (lines 72-79): each affected Tamil text has status `original_only`, display mode `original_with_notice`, provenance `original_only`, reason `no_model_text: call_failed: context_truncated`. So the fallback worked as designed: nothing unverified is shown as verified. The 8 lines are part of the 194 Tamil fallbacks already counted in the official results.

User-visible outcome: in Tamil, those 8 lines (4 per document, including 1 warning in rx_019) appear in the original English with the Tamil notice "no automatic explanation is available for this line; the original text is shown".

## (f) The 3 documents with most of the unmatched (raw hallucinated) medicines

7 of the 13 raw unmatched medicines come from these three documents (ds_010: 3, ds_024: 2, rx_009: 2).

| document | template, difficulty, type | what makes it hard (general terms) |
|---|---|---|
| ds_010 | t2dm_htn, clean, discharge summary | clean layout, but several drugs are printed with brand and generic together and the image readings (photo, poor) merged them into the brand field ("Metformin (Glycomet)") or misspelled a long generic; the matcher compares names, so a combined field scores low |
| ds_024 | gastro, messy, discharge summary | messy prose-like lines with form prefixes ("cap.", "t.") and units attached to numbers; the model put the whole line in the name field (text condition, so not an OCR problem) |
| rx_009 | cap, messy, prescription | numbered list with mixed prefixes (TAB., t., SYP.), brand-in-parentheses, capital-letter units ("625MG", "30 MG/5 ML"); the model again put brand, generic and form in one field |

Common pattern: brand, generic and form text in one field. These raw misses are matching failures from field placement; after the rules, all three documents match in every condition except the one ds_028 row of case (d).

User-visible outcome: none of the 7 raw misses survives to the user as a missing medicine, because the rule layer separates the names; the raw numbers describe the model's output before that step.
