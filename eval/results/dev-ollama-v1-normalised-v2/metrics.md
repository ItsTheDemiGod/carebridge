# dev-ollama-v1-normalised-v2

Re-scored from cached raw outputs of `dev-ollama-v1` (no model calls). Medicines pair with ground truth if EITHER raw or normalised names match. Unreadable raw files: none.

## Headline metrics (raw / normalised)

| metric | text | clean | scan | photo | poor | all |
|---|---|---|---|---|---|---|
| med_precision | 0.9643 / 1.0 | 0.9881 / 1.0 | 0.9881 / 1.0 | 0.9881 / 1.0 | 0.9881 / 0.9881 | 0.9833 / 0.9976 |
| med_recall | 0.9643 / 1.0 | 0.9881 / 1.0 | 0.9881 / 1.0 | 0.9881 / 1.0 | 0.9881 / 0.9881 | 0.9833 / 0.9976 |
| med_f1 | 0.9643 / 1.0 | 0.9881 / 1.0 | 0.9881 / 1.0 | 0.9881 / 1.0 | 0.9881 / 0.9881 | 0.9833 / 0.9976 |
| med_fully_correct_rate | 0.3086 / 0.869 | 0.3976 / 0.8571 | 0.2892 / 0.7857 | 0.241 / 0.8214 | 0.3012 / 0.7229 | 0.3075 / 0.8115 |
| hallucinated_meds | 3 / 0 | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 1 | 7 / 1 |
| invented_value_rate | 0.2 / 0.0439 | 0.2193 / 0.0526 | 0.3482 / 0.0526 | 0.3125 / 0.0439 | 0.3482 / 0.0893 | 0.2857 / 0.0563 |
| followup_precision | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| followup_recall | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| redflag_precision | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| redflag_recall | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| quote_exact_rate | 0.8994 / 0.8994 | 0.8742 / 0.8742 | 0.7925 / 0.7925 | 0.7862 / 0.7862 | 0.7044 / 0.7044 | 0.8113 / 0.8113 |
| quote_norm_exact_rate | 0.9748 / 0.9748 | 0.9748 / 0.9748 | 0.8994 / 0.8994 | 0.9057 / 0.9057 | 0.8239 / 0.8239 | 0.9157 / 0.9157 |
| quote_strict_rate | 0.9748 / 0.9748 | 0.9937 / 0.9937 | 0.9497 / 0.9497 | 0.9623 / 0.9623 | 0.8868 / 0.8868 | 0.9535 / 0.9535 |
| quote_fuzzy_rate | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |

## Per-field accuracy (raw / normalised)

| metric | text | clean | scan | photo | poor | all |
|---|---|---|---|---|---|---|
| acc_strength | 0.9753 / 0.9762 | 0.9639 / 0.9643 | 0.9639 / 0.9643 | 0.9518 / 0.9524 | 0.9277 / 0.9277 | 0.9564 / 0.957 |
| acc_form | 0.9506 / 0.9524 | 0.988 / 0.9881 | 0.9759 / 0.9762 | 0.9759 / 0.9762 | 0.988 / 0.988 | 0.9758 / 0.9761 |
| acc_dose | 0.9506 / 0.9524 | 0.9518 / 0.9524 | 0.9639 / 0.9643 | 0.9759 / 0.9762 | 0.9398 / 0.9398 | 0.9564 / 0.957 |
| acc_times_per_day | 0.9383 / 0.9643 | 0.9398 / 0.9643 | 0.9157 / 0.9643 | 0.9157 / 0.9643 | 0.9277 / 0.9518 | 0.9274 / 0.9618 |
| acc_timing_label | 0.7037 / 0.9881 | 0.7711 / 1.0 | 0.747 / 0.9881 | 0.6867 / 1.0 | 0.7349 / 0.9759 | 0.7288 / 0.9905 |
| acc_is_prn | 1.0 / 1.0 | 1.0 / 1.0 | 0.988 / 0.9881 | 0.988 / 0.9881 | 0.988 / 0.988 | 0.9927 / 0.9928 |
| acc_duration_days | 1.0 / 1.0 | 0.9398 / 0.9881 | 0.9157 / 0.9643 | 0.9157 / 0.9643 | 0.8795 / 0.9277 | 0.9298 / 0.969 |
| acc_brand_name | 0.716 / 1.0 | 0.6867 / 1.0 | 0.6867 / 0.9643 | 0.5904 / 0.9762 | 0.6867 / 0.9518 | 0.6731 / 0.9785 |
| acc_generic_name | 0.8272 / 1.0 | 0.8313 / 1.0 | 0.6627 / 1.0 | 0.6988 / 0.9762 | 0.6506 / 0.9518 | 0.7337 / 0.9857 |
| exact_ci_brand_name | 0.3827 / 1.0 | 0.5783 / 1.0 | 0.6145 / 0.9643 | 0.5181 / 0.9762 | 0.6145 / 0.9518 | 0.5424 / 0.9785 |
| exact_ci_generic_name | 0.8272 / 1.0 | 0.8313 / 1.0 | 0.6506 / 1.0 | 0.6988 / 0.9762 | 0.6506 / 0.9518 | 0.7312 / 0.9857 |

Quote checks cover every item quote (medicines, follow-ups, red flags). exact = byte match; norm_exact = after Unicode/case/whitespace/punctuation normalisation; strict = norm_exact or a near-contiguous match (ratio >= 0.95 AND identical digits). quote_fuzzy is the OLD loose check (0.9), kept for comparison.

Strict-quote failures: text: 0 digit mismatch / 4 low similarity, clean: 1 digit mismatch / 0 low similarity, scan: 3 digit mismatch / 5 low similarity, photo: 3 digit mismatch / 3 low similarity, poor: 6 digit mismatch / 12 low similarity, all: 13 digit mismatch / 24 low similarity

## Review levels (app mode: model output only)

must_confirm is the detector. Errors are counted on the final (normalised) values; an unpaired predicted medicine counts as a name error.

| condition | medicines | must_confirm | share | name errors | name P | name R | name unflagged | timing errors | timing P | timing R | timing unflagged |
|---|---|---|---|---|---|---|---|---|---|---|---|
| text | 84 | 25 | 0.298 | 0 | 0.0 | None | 0 | 1 | 0.04 | 1.0 | 0 |
| clean | 84 | 33 | 0.393 | 0 | 0.0 | None | 0 | 0 | 0.0 | None | 0 |
| scan | 84 | 42 | 0.5 | 3 | 0.071 | 1.0 | 0 | 1 | 0.0 | 0.0 | 1 |
| photo | 84 | 45 | 0.536 | 4 | 0.089 | 1.0 | 0 | 0 | 0.0 | None | 0 |
| poor | 84 | 49 | 0.583 | 7 | 0.143 | 1.0 | 0 | 2 | 0.041 | 1.0 | 0 |
| all | 420 | 194 | 0.462 | 14 | 0.072 | 1.0 | 0 | 4 | 0.015 | 0.75 | 1 |

Pooled by level: must_confirm: 194 medicines, 14 name / 3 timing / 62 any errors; note: 79 medicines, 0 name / 0 timing / 10 any errors; none: 147 medicines, 0 name / 1 timing / 8 any errors
With document text (adds quote_not_in_document): must_confirm 196 of 420, name unflagged 0, timing unflagged 0.
Phase 2h (all flags except audit-only): 133 of 420 flagged; name precision 0.098, name recall 0.929, name unflagged 1; timing precision 0.023, recall 0.75, timing unflagged 1.

## Flag breakdown (app mode, pooled)

precision = share of medicines carrying the flag that have any remaining error (name / timing columns are field specific)

| flag | medicines | with any error | precision | name errors | name precision | timing errors | timing precision | share of erroneous medicines caught |
|---|---|---|---|---|---|---|---|---|
| conflict_timing_label | 109 | 23 | 0.211 | 4 | 0.037 | 0 | 0.0 | 0.287 |
| role_corrected | 61 | 10 | 0.164 | 1 | 0.016 | 0 | 0.0 | 0.125 |
| duplicate_name_fields | 59 | 14 | 0.237 | 3 | 0.051 | 2 | 0.034 | 0.175 |
| near_miss_name | 38 | 19 | 0.5 | 10 | 0.263 | 1 | 0.026 | 0.237 |
| name_not_in_quote | 19 | 2 | 0.105 | 1 | 0.053 | 0 | 0.0 | 0.025 |
| conflict_duration_days | 18 | 4 | 0.222 | 0 | 0.0 | 0 | 0.0 | 0.05 |
| incomplete_quote | 18 | 15 | 0.833 | 1 | 0.056 | 3 | 0.167 | 0.188 |
| unusual_strength | 16 | 16 | 1.0 | 0 | 0.0 | 0 | 0.0 | 0.2 |
| non_daily_frequency | 15 | 15 | 1.0 | 0 | 0.0 | 1 | 0.067 | 0.188 |
| conflict_times_per_day | 13 | 7 | 0.538 | 0 | 0.0 | 0 | 0.0 | 0.087 |
| unresolved_name | 8 | 8 | 1.0 | 8 | 1.0 | 1 | 0.125 | 0.1 |

## Readiness (app mode)

| condition | medicines | interaction_ready | schedule_ready | WRONG resolved_generic among interaction_ready | wrong schedule among schedule_ready |
|---|---|---|---|---|---|
| text | 84 | 59 | 48 | 0 | 0 |
| clean | 84 | 51 | 39 | 0 | 0 |
| scan | 84 | 42 | 35 | 0 | 1 |
| photo | 84 | 39 | 30 | 0 | 0 |
| poor | 84 | 35 | 28 | 0 | 0 |
| all | 420 | 226 | 180 | 0 | 1 |

Wrong resolved_generic cases: none

### Remaining name errors not at must_confirm (0); up to 10

- none

### Remaining timing errors not at must_confirm (1); up to 10

- {'cond': 'scan', 'doc': 'ds_008', 'level': 'none', 'pred': 'unspecified', 'gt': 'before_meals', 'quote': 'Tab. Pantoprazole 40 mg 1 tab OD x 5/7'}

### Medicine quotes failing the document check (23); up to 10

- {'cond': 'clean', 'doc': 'ds_011', 'quote': 'SYP AMBROXOL 30 MG/S ML 5 mL TDS X 5D'}
- {'cond': 'photo', 'doc': 'ds_011', 'quote': '4) SYP AMBROXOL 30 MG/S ML 5 mL TDS X SD'}
- {'cond': 'photo', 'doc': 'ds_027', 'quote': 'T. SHELICAL 500 MG 1 tab PC FOR 380'}
- {'cond': 'photo', 'doc': 'ds_027', 'quote': 'CAP D-RISE 60000IU 1 cap once weekly X B WEEKS'}
- {'cond': 'photo', 'doc': 'ds_036', 'quote': '3. T. CALCIUM CARBONATE + VITAMIN D3 600MG 1-0-0 PC FOR 30D'}
- {'cond': 'poor', 'doc': 'ds_008', 'quote': 'Tab. Pantoprazole 40 mg 1 tab AC x 5/7'}
- {'cond': 'poor', 'doc': 'ds_011', 'quote': 'Tab Crocin 65mg 1 tab SOS'}
- {'cond': 'poor', 'doc': 'ds_011', 'quote': 'SVP AMBROXOL 30 MG/S ML 5 mL TDS X SD'}
- {'cond': 'poor', 'doc': 'ds_018', 'quote': 't. calcium carbonate + vitamin d3 500mg 1 tab od for 365'}
- {'cond': 'poor', 'doc': 'ds_020', 'quote': 'TAB. CALPOL 500 MG 1 tab SOS'}

Near-miss names (not an exact formulary name, within edit distance): raw 43, normalised 7
