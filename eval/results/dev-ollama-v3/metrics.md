# Run dev-ollama-v3

split=dev prompt=v3 oracle=False docs=20 api_calls=100 api_failed_not_scored=0 cache_hits=0 tokens=332637 mean_latency_s=30.04

### Coverage (documents attempted / scored / SKIPPED)

| condition | attempted | scored | skipped | skip reasons | latency median s | latency p95 s |
|---|---|---|---|---|---|---|
| text | 20 | 20 | 0 | - | 27.4 | 37.6 |
| clean | 20 | 20 | 0 | - | 30.1 | 40.4 |
| scan | 20 | 20 | 0 | - | 31.0 | 41.3 |
| photo | 20 | 20 | 0 | - | 30.2 | 40.7 |
| poor | 20 | 20 | 0 | - | 30.7 | 40.7 |

### Drug-name sanity (predicted names with no formulary match >= 0.8)

| condition | names | unmatched | rate |
|---|---|---|---|
| text | 127 | 13 | 0.102 |
| clean | 123 | 9 | 0.073 |
| scan | 127 | 14 | 0.11 |
| photo | 135 | 13 | 0.096 |
| poor | 139 | 11 | 0.079 |

Examples (condition, doc, predicted, closest formulary, ratio):
- ('text', 'ds_008', 'Prednisolone (Omnacortil)', 'prednisolone', 0.65)
- ('text', 'ds_008', 'Budesonide + Formoterol (Symbicort)', 'budesonide + formoterol', 0.79)
- ('text', 'ds_026', 'INHALER TIOVA', 'tiova', 0.56)
- ('text', 'ds_026', 'Inhaler Ventolin', 'ventolin', 0.67)
- ('text', 'ds_032', 'TAB CROCIN (PARACETAMOL)', 'paracetamol', 0.71)
- ('text', 'rx_001', 'Metformin (Glucophage)', 'glucophage', 0.62)
- ('text', 'rx_003', 'Tab Dolo 500mg', 'dolo', 0.57)
- ('text', 'rx_003', 'TAB DOMSTAL 10 MG', 'domstal', 0.7)
- ('text', 'rx_005', 'Tab Azithromycin (Azithral)', 'azithromycin', 0.69)
- ('text', 'rx_005', 'Inh. Budesonide + Formoterol (Foracort)', 'budesonide + formoterol', 0.74)

### By overall

| metric | all |
|---|---|
| docs | 100 |
| med_precision | 0.981 |
| med_recall | 0.981 |
| med_f1 | 0.981 |
| med_fully_correct_rate | 0.2306 |
| followup_recall | 1.0 |
| followup_days_accuracy | 0.8667 |
| redflag_recall | 1.0 |
| hallucinated_meds | 8 |
| invented_value_rate | 0.3971 |
| quote_exact_rate | 0.7862 |
| quote_fuzzy_rate | 0.9987 |
| parse_failure_rate | 0.0 |
| low_confidence_rate | 0.0 |
| acc_strength | 0.9612 |
| acc_form | 0.9782 |
| acc_dose | 0.9587 |
| acc_times_per_day | 0.9175 |
| acc_timing_label | 0.8058 |
| acc_is_prn | 0.9976 |
| acc_duration_days | 0.9126 |
| acc_brand_name | 0.5655 |
| acc_generic_name | 0.6262 |

### By condition

| metric | text | clean | scan | photo | poor |
|---|---|---|---|---|---|
| docs | 20 | 20 | 20 | 20 | 20 |
| med_precision | 0.9762 | 1.0 | 0.9643 | 0.9762 | 0.9881 |
| med_recall | 0.9762 | 1.0 | 0.9643 | 0.9762 | 0.9881 |
| med_f1 | 0.9762 | 1.0 | 0.9643 | 0.9762 | 0.9881 |
| med_fully_correct_rate | 0.2927 | 0.3095 | 0.1852 | 0.1951 | 0.1687 |
| followup_recall | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| followup_days_accuracy | 0.8095 | 0.9048 | 0.8095 | 0.9048 | 0.9048 |
| redflag_recall | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| hallucinated_meds | 2 | 0 | 3 | 2 | 1 |
| invented_value_rate | 0.3333 | 0.3333 | 0.4054 | 0.4595 | 0.4554 |
| quote_exact_rate | 0.805 | 0.8679 | 0.7736 | 0.7799 | 0.7044 |
| quote_fuzzy_rate | 1.0 | 1.0 | 1.0 | 0.9937 | 1.0 |
| parse_failure_rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| low_confidence_rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| acc_strength | 1.0 | 0.9405 | 0.963 | 0.9634 | 0.9398 |
| acc_form | 0.9634 | 0.9881 | 0.9753 | 0.9756 | 0.988 |
| acc_dose | 0.9512 | 0.9524 | 0.963 | 0.9756 | 0.9518 |
| acc_times_per_day | 0.9512 | 0.9405 | 0.8889 | 0.8902 | 0.9157 |
| acc_timing_label | 0.8293 | 0.8214 | 0.7778 | 0.7927 | 0.8072 |
| acc_is_prn | 1.0 | 1.0 | 1.0 | 0.9878 | 1.0 |
| acc_duration_days | 0.9756 | 0.9524 | 0.9012 | 0.878 | 0.8554 |
| acc_brand_name | 0.5732 | 0.6071 | 0.5679 | 0.5244 | 0.5542 |
| acc_generic_name | 0.6585 | 0.6786 | 0.6296 | 0.5732 | 0.5904 |

### By difficulty

| metric | messy | abbreviated | clean |
|---|---|---|---|
| docs | 30 | 45 | 25 |
| med_precision | 0.9667 | 0.9842 | 0.9909 |
| med_recall | 0.9667 | 0.9842 | 0.9909 |
| med_f1 | 0.9667 | 0.9842 | 0.9909 |
| med_fully_correct_rate | 0.3017 | 0.2032 | 0.2018 |
| followup_recall | 1.0 | 1.0 | 1.0 |
| followup_days_accuracy | 0.5333 | 1.0 | 1.0 |
| redflag_recall | 1.0 | 1.0 | 1.0 |
| hallucinated_meds | 4 | 3 | 1 |
| invented_value_rate | 0.4023 | 0.3596 | 0.4746 |
| quote_exact_rate | 0.6213 | 0.7914 | 0.9619 |
| quote_fuzzy_rate | 1.0 | 0.9971 | 1.0 |
| parse_failure_rate | 0.0 | 0.0 | 0.0 |
| low_confidence_rate | 0.0 | 0.0 | 0.0 |
| acc_strength | 0.9052 | 0.9733 | 1.0 |
| acc_form | 0.9483 | 0.984 | 1.0 |
| acc_dose | 0.9569 | 0.9358 | 1.0 |
| acc_times_per_day | 0.8621 | 0.9037 | 1.0 |
| acc_timing_label | 0.8793 | 0.6791 | 0.945 |
| acc_is_prn | 1.0 | 0.9947 | 1.0 |
| acc_duration_days | 0.8793 | 0.8824 | 1.0 |
| acc_brand_name | 0.6638 | 0.6738 | 0.2752 |
| acc_generic_name | 0.6552 | 0.615 | 0.6147 |

### By split

| metric | dev |
|---|---|
| docs | 100 |
| med_precision | 0.981 |
| med_recall | 0.981 |
| med_f1 | 0.981 |
| med_fully_correct_rate | 0.2306 |
| followup_recall | 1.0 |
| followup_days_accuracy | 0.8667 |
| redflag_recall | 1.0 |
| hallucinated_meds | 8 |
| invented_value_rate | 0.3971 |
| quote_exact_rate | 0.7862 |
| quote_fuzzy_rate | 0.9987 |
| parse_failure_rate | 0.0 |
| low_confidence_rate | 0.0 |
| acc_strength | 0.9612 |
| acc_form | 0.9782 |
| acc_dose | 0.9587 |
| acc_times_per_day | 0.9175 |
| acc_timing_label | 0.8058 |
| acc_is_prn | 0.9976 |
| acc_duration_days | 0.9126 |
| acc_brand_name | 0.5655 |
| acc_generic_name | 0.6262 |

