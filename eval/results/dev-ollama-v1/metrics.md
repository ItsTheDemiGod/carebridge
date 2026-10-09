# Run dev-ollama-v1

split=dev prompt=v1 oracle=False docs=20 api_calls=93 api_failed_not_scored=0 cache_hits=7 tokens=309348 mean_latency_s=29.45

### Coverage (documents attempted / scored / SKIPPED)

| condition | attempted | scored | skipped | skip reasons | latency median s | latency p95 s |
|---|---|---|---|---|---|---|
| text | 20 | 20 | 0 | - | 27.5 | 37.9 |
| clean | 20 | 20 | 0 | - | 29.9 | 40.7 |
| scan | 20 | 20 | 0 | - | 30.4 | 41.1 |
| photo | 20 | 20 | 0 | - | 30.1 | 40.7 |
| poor | 20 | 20 | 0 | - | 30.3 | 41.3 |

### Drug-name sanity (predicted names with no formulary match >= 0.8)

| condition | names | unmatched | rate |
|---|---|---|---|
| text | 113 | 15 | 0.133 |
| clean | 114 | 5 | 0.044 |
| scan | 126 | 6 | 0.048 |
| photo | 122 | 4 | 0.033 |
| poor | 128 | 3 | 0.023 |

Examples (condition, doc, predicted, closest formulary, ratio):
- ('text', 'ds_020', 'Syrup Ambrodil (Ambroxol)', 'ambrodil', 0.59)
- ('text', 'ds_025', 'Lipitor (Atorvastatin)', 'atorvastatin', 0.71)
- ('text', 'ds_025', 'Pantoprazole (Pantop)', 'pantoprazole', 0.73)
- ('text', 'ds_026', 'INHALER TIOVA', 'tiova', 0.56)
- ('text', 'ds_026', 'Inhaler Ventolin', 'ventolin', 0.67)
- ('text', 'ds_027', 'inj enoxaparin (lovenox)', 'enoxaparin', 0.67)
- ('text', 'ds_032', 'TAB CROCIN (PARACETAMOL)', 'paracetamol', 0.71)
- ('text', 'rx_001', 'Metformin (Glucophage)', 'glucophage', 0.62)
- ('text', 'rx_003', 'Tab Dolo 500mg', 'dolo', 0.57)
- ('text', 'rx_005', 'Tab Azithromycin (Azithral)', 'azithromycin', 0.69)

### By overall

| metric | all |
|---|---|
| docs | 100 |
| med_precision | 0.9833 |
| med_recall | 0.9833 |
| med_f1 | 0.9833 |
| med_fully_correct_rate | 0.3075 |
| followup_recall | 1.0 |
| followup_days_accuracy | 0.8952 |
| redflag_recall | 1.0 |
| hallucinated_meds | 7 |
| invented_value_rate | 0.2857 |
| quote_exact_rate | 0.8113 |
| quote_fuzzy_rate | 1.0 |
| parse_failure_rate | 0.0 |
| low_confidence_rate | 0.0 |
| acc_strength | 0.9564 |
| acc_form | 0.9758 |
| acc_dose | 0.9564 |
| acc_times_per_day | 0.9274 |
| acc_timing_label | 0.7288 |
| acc_is_prn | 0.9927 |
| acc_duration_days | 0.9298 |
| acc_brand_name | 0.6731 |
| acc_generic_name | 0.7337 |

### By condition

| metric | text | clean | scan | photo | poor |
|---|---|---|---|---|---|
| docs | 20 | 20 | 20 | 20 | 20 |
| med_precision | 0.9643 | 0.9881 | 0.9881 | 0.9881 | 0.9881 |
| med_recall | 0.9643 | 0.9881 | 0.9881 | 0.9881 | 0.9881 |
| med_f1 | 0.9643 | 0.9881 | 0.9881 | 0.9881 | 0.9881 |
| med_fully_correct_rate | 0.3086 | 0.3976 | 0.2892 | 0.241 | 0.3012 |
| followup_recall | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| followup_days_accuracy | 0.8095 | 0.9048 | 0.8571 | 0.9524 | 0.9524 |
| redflag_recall | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| hallucinated_meds | 3 | 1 | 1 | 1 | 1 |
| invented_value_rate | 0.2 | 0.2193 | 0.3482 | 0.3125 | 0.3482 |
| quote_exact_rate | 0.8994 | 0.8742 | 0.7925 | 0.7862 | 0.7044 |
| quote_fuzzy_rate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| parse_failure_rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| low_confidence_rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| acc_strength | 0.9753 | 0.9639 | 0.9639 | 0.9518 | 0.9277 |
| acc_form | 0.9506 | 0.988 | 0.9759 | 0.9759 | 0.988 |
| acc_dose | 0.9506 | 0.9518 | 0.9639 | 0.9759 | 0.9398 |
| acc_times_per_day | 0.9383 | 0.9398 | 0.9157 | 0.9157 | 0.9277 |
| acc_timing_label | 0.7037 | 0.7711 | 0.747 | 0.6867 | 0.7349 |
| acc_is_prn | 1.0 | 1.0 | 0.988 | 0.988 | 0.988 |
| acc_duration_days | 1.0 | 0.9398 | 0.9157 | 0.9157 | 0.8795 |
| acc_brand_name | 0.716 | 0.6867 | 0.6867 | 0.5904 | 0.6867 |
| acc_generic_name | 0.8272 | 0.8313 | 0.6627 | 0.6988 | 0.6506 |

### By difficulty

| metric | messy | abbreviated | clean |
|---|---|---|---|
| docs | 30 | 45 | 25 |
| med_precision | 0.9833 | 0.9842 | 0.9818 |
| med_recall | 0.9833 | 0.9842 | 0.9818 |
| med_f1 | 0.9833 | 0.9842 | 0.9818 |
| med_fully_correct_rate | 0.2966 | 0.246 | 0.4259 |
| followup_recall | 1.0 | 1.0 | 1.0 |
| followup_days_accuracy | 0.6333 | 1.0 | 1.0 |
| redflag_recall | 1.0 | 1.0 | 1.0 |
| hallucinated_meds | 2 | 3 | 2 |
| invented_value_rate | 0.322 | 0.2444 | 0.3248 |
| quote_exact_rate | 0.617 | 0.8429 | 0.9762 |
| quote_fuzzy_rate | 1.0 | 1.0 | 1.0 |
| parse_failure_rate | 0.0 | 0.0 | 0.0 |
| low_confidence_rate | 0.0 | 0.0 | 0.0 |
| acc_strength | 0.9068 | 0.9626 | 1.0 |
| acc_form | 0.9407 | 0.984 | 1.0 |
| acc_dose | 0.9576 | 0.9305 | 1.0 |
| acc_times_per_day | 0.8729 | 0.9198 | 1.0 |
| acc_timing_label | 0.7627 | 0.6203 | 0.8796 |
| acc_is_prn | 0.9831 | 0.9947 | 1.0 |
| acc_duration_days | 0.8729 | 0.9251 | 1.0 |
| acc_brand_name | 0.7458 | 0.7059 | 0.537 |
| acc_generic_name | 0.7966 | 0.6952 | 0.7315 |

### By split

| metric | dev |
|---|---|
| docs | 100 |
| med_precision | 0.9833 |
| med_recall | 0.9833 |
| med_f1 | 0.9833 |
| med_fully_correct_rate | 0.3075 |
| followup_recall | 1.0 |
| followup_days_accuracy | 0.8952 |
| redflag_recall | 1.0 |
| hallucinated_meds | 7 |
| invented_value_rate | 0.2857 |
| quote_exact_rate | 0.8113 |
| quote_fuzzy_rate | 1.0 |
| parse_failure_rate | 0.0 |
| low_confidence_rate | 0.0 |
| acc_strength | 0.9564 |
| acc_form | 0.9758 |
| acc_dose | 0.9564 |
| acc_times_per_day | 0.9274 |
| acc_timing_label | 0.7288 |
| acc_is_prn | 0.9927 |
| acc_duration_days | 0.9298 |
| acc_brand_name | 0.6731 |
| acc_generic_name | 0.7337 |

