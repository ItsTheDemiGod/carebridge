# dev-ollama-v1-normalised

Re-scored from cached raw outputs of `dev-ollama-v1` (no model calls). Medicines are paired with ground truth if EITHER their raw or their normalised names match. Documents unreadable: none.

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

## Near-miss names (not an exact formulary name, within edit distance)

raw total 43, normalised total 7

Examples (normalised): photo/ds_023: Caipol ~ calpol (0.83); photo/ds_037: Telms ~ telma (0.8); poor/ds_018: ENDOKAPARIN ~ enoxaparin (0.86); poor/ds_026: Vertolin ~ ventolin (0.88); poor/rx_005: Mysolone ~ wysolone (0.88); scan/ds_032: Cap Niffran ~ niftran (0.86); scan/rx_003: Tab Dol ~ dolo (0.86)

## Invented values by field (raw / normalised): role confusion | in document, wrong field | made up (appears nowhere in the document); out of ground-truth-null cells

| field | of null | raw invented | raw role | raw in_doc | raw made_up | norm invented | norm role | norm in_doc | norm made_up |
|---|---|---|---|---|---|---|---|---|---|
| strength | 10 | 10 | 0 | 10 | 0 | 10 | 0 | 10 | 0 |
| dose | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| times_per_day | 79 | 20 | 0 | 20 | 0 | 16 | 0 | 16 | 0 |
| duration_days | 180 | 4 | 0 | 3 | 1 | 4 | 0 | 3 | 1 |
| brand_name | 114 | 85 | 84 | 0 | 1 | 1 | 0 | 0 | 1 |
| generic_name | 177 | 41 | 15 | 2 | 24 | 1 | 0 | 0 | 1 |

## Flag effectiveness (normalised, all conditions)

Detector A = needs_verification (any flag or low confidence); detector B = only the flags specific to that field.

| field | meds | remaining errors | A recall | A precision | A unflagged | B recall | B precision | B unflagged |
|---|---|---|---|---|---|---|---|---|
| name | 420 | 14 | 0.929 | 0.098 | 1 | 0.929 | 0.119 | 1 |
| timing | 420 | 4 | 0.75 | 0.023 | 1 | 0.25 | 0.067 | 3 |

Medications needing verification: 133 of 420. Rule overrode a model timing label 109 times.

Flag counts: conflict_timing_label=109, role_corrected=61, duplicate_name_fields=59, near_miss_name=38, name_not_in_quote=19, conflict_duration_days=18, unusual_strength=16, non_daily_frequency=15, conflict_times_per_day=13, unresolved_name=8

### Unflagged name errors (1); up to 10 examples

- {'condition': 'scan', 'doc': 'ds_026', 'predicted': [None, 'Pantoprazole'], 'ground_truth': ['PANTOP', 'PANTOPRAZOLE'], 'quote': '6) TAB PANTOPRAZOLE 40 MG 1-0-0 AC X 5/7'}

### Unflagged timing errors (1); up to 10 examples

- {'condition': 'scan', 'doc': 'ds_008', 'predicted': 'unspecified', 'ground_truth': 'before_meals', 'quote': 'Tab. Pantoprazole 40 mg 1 tab OD x 5/7'}
