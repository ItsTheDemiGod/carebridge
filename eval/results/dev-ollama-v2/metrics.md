# Run dev-ollama-v2

split=dev prompt=v2 oracle=False docs=20 api_calls=100 api_failed_not_scored=0 cache_hits=0 tokens=329600 mean_latency_s=30.3

### Coverage (documents attempted / scored / SKIPPED)

| condition | attempted | scored | skipped | skip reasons | latency median s | latency p95 s |
|---|---|---|---|---|---|---|
| text | 20 | 20 | 0 | - | 27.8 | 39.0 |
| clean | 20 | 20 | 0 | - | 30.1 | 40.1 |
| scan | 20 | 20 | 0 | - | 30.9 | 41.1 |
| photo | 20 | 20 | 0 | - | 30.1 | 40.8 |
| poor | 20 | 20 | 0 | - | 30.7 | 40.8 |

### Drug-name sanity (predicted names with no formulary match >= 0.8)

| condition | names | unmatched | rate |
|---|---|---|---|
| text | 144 | 51 | 0.354 |
| clean | 143 | 34 | 0.238 |
| scan | 146 | 54 | 0.37 |
| photo | 144 | 48 | 0.333 |
| poor | 135 | 58 | 0.43 |

Examples (condition, doc, predicted, closest formulary, ratio):
- ('text', 'ds_008', 'Tab Prednisolone (Omnacortil)', 'prednisolone', 0.65)
- ('text', 'ds_008', 'Inh Budesonide + Formoterol (Symbicort)', 'budesonide + formoterol', 0.74)
- ('text', 'ds_008', 'INH TIOVA', 'tiova', 0.71)
- ('text', 'ds_011', 'Tab. Augmentin 625mg', 'augmentin', 0.75)
- ('text', 'ds_011', 'T. Azithromycin 500mg', 'azithromycin', 0.73)
- ('text', 'ds_011', 'Tab Crocin 650mg', 'crocin', 0.67)
- ('text', 'ds_011', 'SYP AMBROXOL 30 MG/5 ML', 'ambroxol', 0.59)
- ('text', 'ds_018', 'Cap. D-Rise 60000IU', 'd-rise', 0.6)
- ('text', 'ds_020', 'TAB. AUGMENTIN 625MG', 'augmentin', 0.75)
- ('text', 'ds_020', 'T. Zithromax 500 mg', 'zithromax', 0.64)

### By overall

| metric | all |
|---|---|
| docs | 100 |
| med_precision | 0.8357 |
| med_recall | 0.8357 |
| med_f1 | 0.8357 |
| med_fully_correct_rate | 0.1425 |
| followup_recall | 1.0 |
| followup_days_accuracy | 0.8762 |
| redflag_recall | 1.0 |
| hallucinated_meds | 69 |
| invented_value_rate | 0.474 |
| quote_exact_rate | 0.7711 |
| quote_fuzzy_rate | 1.0 |
| parse_failure_rate | 0.0 |
| low_confidence_rate | 0.0 |
| acc_strength | 0.9658 |
| acc_form | 0.9715 |
| acc_dose | 0.9459 |
| acc_times_per_day | 0.9231 |
| acc_timing_label | 0.8575 |
| acc_is_prn | 0.9972 |
| acc_duration_days | 0.9288 |
| acc_brand_name | 0.4758 |
| acc_generic_name | 0.5926 |

### By condition

| metric | text | clean | scan | photo | poor |
|---|---|---|---|---|---|
| docs | 20 | 20 | 20 | 20 | 20 |
| med_precision | 0.8095 | 0.9405 | 0.8452 | 0.8214 | 0.7619 |
| med_recall | 0.8095 | 0.9405 | 0.8452 | 0.8214 | 0.7619 |
| med_f1 | 0.8095 | 0.9405 | 0.8452 | 0.8214 | 0.7619 |
| med_fully_correct_rate | 0.1618 | 0.2025 | 0.0986 | 0.1014 | 0.1406 |
| followup_recall | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| followup_days_accuracy | 0.8095 | 0.9048 | 0.8571 | 0.9048 | 0.9048 |
| redflag_recall | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| hallucinated_meds | 16 | 5 | 13 | 15 | 20 |
| invented_value_rate | 0.4578 | 0.4312 | 0.4737 | 0.5281 | 0.4884 |
| quote_exact_rate | 0.7673 | 0.8679 | 0.7799 | 0.7233 | 0.717 |
| quote_fuzzy_rate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| parse_failure_rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| low_confidence_rate | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| acc_strength | 0.9853 | 0.962 | 0.9859 | 0.9565 | 0.9375 |
| acc_form | 0.9559 | 0.962 | 0.9859 | 0.971 | 0.9844 |
| acc_dose | 0.9559 | 0.9494 | 0.9437 | 0.971 | 0.9062 |
| acc_times_per_day | 0.9559 | 0.9241 | 0.9155 | 0.8841 | 0.9375 |
| acc_timing_label | 0.8676 | 0.8481 | 0.8451 | 0.8696 | 0.8594 |
| acc_is_prn | 1.0 | 1.0 | 1.0 | 0.9855 | 1.0 |
| acc_duration_days | 0.9706 | 0.9494 | 0.9155 | 0.913 | 0.8906 |
| acc_brand_name | 0.4265 | 0.5823 | 0.4648 | 0.4203 | 0.4688 |
| acc_generic_name | 0.7353 | 0.5949 | 0.5493 | 0.5797 | 0.5 |

### By difficulty

| metric | messy | abbreviated | clean |
|---|---|---|---|
| docs | 30 | 45 | 25 |
| med_precision | 0.9167 | 0.7632 | 0.8727 |
| med_recall | 0.9167 | 0.7632 | 0.8727 |
| med_f1 | 0.9167 | 0.7632 | 0.8727 |
| med_fully_correct_rate | 0.1364 | 0.1586 | 0.125 |
| followup_recall | 1.0 | 1.0 | 1.0 |
| followup_days_accuracy | 0.5667 | 1.0 | 1.0 |
| redflag_recall | 1.0 | 1.0 | 1.0 |
| hallucinated_meds | 10 | 45 | 14 |
| invented_value_rate | 0.5741 | 0.3909 | 0.4757 |
| quote_exact_rate | 0.6085 | 0.78 | 0.9381 |
| quote_fuzzy_rate | 1.0 | 1.0 | 1.0 |
| parse_failure_rate | 0.0 | 0.0 | 0.0 |
| low_confidence_rate | 0.0 | 0.0 | 0.0 |
| acc_strength | 0.9182 | 0.9793 | 1.0 |
| acc_form | 0.9364 | 0.9793 | 1.0 |
| acc_dose | 0.9545 | 0.9034 | 1.0 |
| acc_times_per_day | 0.8727 | 0.9103 | 1.0 |
| acc_timing_label | 0.9182 | 0.7517 | 0.9479 |
| acc_is_prn | 1.0 | 0.9931 | 1.0 |
| acc_duration_days | 0.8909 | 0.9103 | 1.0 |
| acc_brand_name | 0.6091 | 0.5793 | 0.1667 |
| acc_generic_name | 0.4545 | 0.5586 | 0.8021 |

### By split

| metric | dev |
|---|---|
| docs | 100 |
| med_precision | 0.8357 |
| med_recall | 0.8357 |
| med_f1 | 0.8357 |
| med_fully_correct_rate | 0.1425 |
| followup_recall | 1.0 |
| followup_days_accuracy | 0.8762 |
| redflag_recall | 1.0 |
| hallucinated_meds | 69 |
| invented_value_rate | 0.474 |
| quote_exact_rate | 0.7711 |
| quote_fuzzy_rate | 1.0 |
| parse_failure_rate | 0.0 |
| low_confidence_rate | 0.0 |
| acc_strength | 0.9658 |
| acc_form | 0.9715 |
| acc_dose | 0.9459 |
| acc_times_per_day | 0.9231 |
| acc_timing_label | 0.8575 |
| acc_is_prn | 0.9972 |
| acc_duration_days | 0.9288 |
| acc_brand_name | 0.4758 |
| acc_generic_name | 0.5926 |

