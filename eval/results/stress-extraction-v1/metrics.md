# Stress extraction results (stress-extraction-v1)

**stress set, authored, not tuned, not the test split.** 30 authored synthetic prescriptions, clean and photo renders. 30 documents give WIDE intervals; no figure here is a claim of accuracy, reliability or safety.

- Ollama running **0.40.11**, pinned (official final run) **0.40.5** (stated deviation; the pin file is unchanged; stress numbers are not to be compared directly with the official ones).
- Model qwen3-vl:8b-instruct, digest running `0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319` (identical to the pin: True).
- Settings {'num_ctx': 6144, 'num_predict': 3000, 'max_image_side': 1280, 'temperature': 0.0}, extraction prompt v1, git commit `c36ae82801`, started 2026-10-28T18:34:34.

## Pass criteria (pre-registered, both conditions together)

| criterion | result | passed |
|---|---|---|
| P1_silent_misses_not_covered_by_flag | value=0, of_gt_pairs=204 | **True** |
| P2_nondaily_schedule_ready | value=0, of_nondaily_extracted=6, nondaily_in_ground_truth=6 | **True** |
| P3_wrong_resolved_generic_among_interaction_ready | value=0, of_interaction_ready=113, interaction_ready_without_gt_counterpart_reported_separately=0 | **True** |
| P4_overlay_every_extracted_gt_pair_found_at_right_level | value=204, of=204 | **True** |

## Condition `clean` (30 documents scored; failed or skipped: 0)

- precision_raw: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- recall_raw: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- f1_raw: 208/208 = 1.0, Wilson None, document bootstrap [1.0, 1.0]
- precision_normalised: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- recall_normalised: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- f1_normalised: 208/208 = 1.0, Wilson None, document bootstrap [1.0, 1.0]
- found_rate: 38/102 = 0.3725, Wilson [0.2849, 0.4694], document bootstrap [0.1321, 0.631]
- found_right_level_rate: 38/102 = 0.3725, Wilson [0.2849, 0.4694], document bootstrap [0.1321, 0.631]
- counts: {'gt_meds': 104, 'pred_meds': 104, 'tp_raw': 104, 'pred_raw': 104, 'tp_norm': 104, 'hallucinated': 0, 'review_none': 50, 'review_must_confirm': 48, 'gt_pairs': 102, 'strict_silent_misses': 64, 'unconfirmed': 64, 'dup_gt_groups': 3, 'dup_notices': 3, 'dup_groups_flagged': 3, 'unusual_flags_total': 3, 'name_flags_total': 6, 'ir_total': 56, 'ir_wrong_generic': 0, 'ov_gt_pairs_extracted': 102, 'ov_found_right_level': 102, 'ov_false_alarms': 0, 'ov_equal_to_gt_mode': 30, 'ov_newly_found': 64, 'found': 38, 'found_right_level': 38, 'false_alarms': 0, 'review_note': 6, 'garbled_gt': 3, 'garbled_flagged': 3, 'garbled_interaction_ready': 0, 'nondaily_gt': 3, 'nondaily_schedule_ready': 0, 'nondaily_flagged': 3, 'unusual_doc_flagged': 3, 'eye_extracted': 3, 'eye_ambiguous_OD': 3, 'eye_schedule_ready': 0, 'eye_interaction_ready': 0, 'eye_any_flag': 3, 'eye_gt': 3}
- ground-truth pair levels: {'major': 5, 'unknown': 46, 'moderate': 47, 'minor': 4}; found levels: {'major': 1, 'unknown': 20, 'moderate': 16, 'minor': 1}; unconfirmed causes: {'role_corrected': 32, 'duplicate_name_fields': 52, 'incomplete_quote': 9, 'unusual_strength': 2}; other outcomes: {}

| category | docs | gt meds | detected (norm) | halluc. | gt pairs | found | unconfirmed | silent not flag-covered | false alarms | overlay right/of |
|---|---|---|---|---|---|---|---|---|---|---|
| major_pair | 3 | 9 | 9 | 0 | 8 | 3 | 5 | 0 | 0 | 8/8 |
| moderate_pair | 3 | 9 | 9 | 0 | 5 | 1 | 4 | 0 | 0 | 5/5 |
| supplement_pair | 3 | 9 | 9 | 0 | 3 | 2 | 1 | 0 | 0 | 3/3 |
| duplicate | 3 | 9 | 9 | 0 | 2 | 0 | 2 | 0 | 0 | 2/2 |
| garbled_name | 3 | 9 | 9 | 0 | 2 | 2 | 0 | 0 | 0 | 2/2 |
| weekly | 3 | 9 | 9 | 0 | 1 | 0 | 1 | 0 | 0 | 1/1 |
| unusual_strength | 3 | 6 | 6 | 0 | 2 | 0 | 2 | 0 | 0 | 2/2 |
| eye_drop_od | 3 | 9 | 9 | 0 | 1 | 1 | 0 | 0 | 0 | 1/1 |
| long_list | 3 | 24 | 24 | 0 | 78 | 29 | 49 | 0 | 0 | 78/78 |
| control | 3 | 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 |

## Condition `photo` (30 documents scored; failed or skipped: 0)

- precision_raw: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- recall_raw: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- f1_raw: 208/208 = 1.0, Wilson None, document bootstrap [1.0, 1.0]
- precision_normalised: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- recall_normalised: 104/104 = 1.0, Wilson [0.9644, 1.0], document bootstrap [1.0, 1.0]
- f1_normalised: 208/208 = 1.0, Wilson None, document bootstrap [1.0, 1.0]
- found_rate: 38/102 = 0.3725, Wilson [0.2849, 0.4694], document bootstrap [0.1321, 0.631]
- found_right_level_rate: 38/102 = 0.3725, Wilson [0.2849, 0.4694], document bootstrap [0.1321, 0.631]
- counts: {'gt_meds': 104, 'pred_meds': 104, 'tp_raw': 104, 'pred_raw': 104, 'tp_norm': 104, 'hallucinated': 0, 'review_none': 50, 'review_must_confirm': 47, 'gt_pairs': 102, 'strict_silent_misses': 64, 'unconfirmed': 64, 'dup_gt_groups': 3, 'dup_notices': 3, 'dup_groups_flagged': 3, 'unusual_flags_total': 3, 'name_flags_total': 6, 'ir_total': 57, 'ir_wrong_generic': 0, 'ov_gt_pairs_extracted': 102, 'ov_found_right_level': 102, 'ov_false_alarms': 2, 'ov_equal_to_gt_mode': 29, 'ov_newly_found': 64, 'found': 38, 'found_right_level': 38, 'false_alarms': 0, 'review_note': 7, 'garbled_gt': 3, 'garbled_flagged': 2, 'garbled_interaction_ready': 0, 'nondaily_gt': 3, 'nondaily_schedule_ready': 0, 'nondaily_flagged': 3, 'unusual_doc_flagged': 3, 'eye_extracted': 3, 'eye_ambiguous_OD': 3, 'eye_schedule_ready': 0, 'eye_interaction_ready': 0, 'eye_any_flag': 3, 'eye_gt': 3}
- ground-truth pair levels: {'major': 5, 'unknown': 46, 'moderate': 47, 'minor': 4}; found levels: {'major': 1, 'unknown': 21, 'moderate': 15, 'minor': 1}; unconfirmed causes: {'duplicate_name_fields': 54, 'role_corrected': 23, 'unusual_strength': 2, 'incomplete_quote': 13, 'unresolved_name': 7, 'near_miss_name': 7}; other outcomes: {}

| category | docs | gt meds | detected (norm) | halluc. | gt pairs | found | unconfirmed | silent not flag-covered | false alarms | overlay right/of |
|---|---|---|---|---|---|---|---|---|---|---|
| major_pair | 3 | 9 | 9 | 0 | 8 | 3 | 5 | 0 | 0 | 8/8 |
| moderate_pair | 3 | 9 | 9 | 0 | 5 | 1 | 4 | 0 | 0 | 5/5 |
| supplement_pair | 3 | 9 | 9 | 0 | 3 | 2 | 1 | 0 | 0 | 3/3 |
| duplicate | 3 | 9 | 9 | 0 | 2 | 0 | 2 | 0 | 0 | 2/2 |
| garbled_name | 3 | 9 | 9 | 0 | 2 | 2 | 0 | 0 | 0 | 2/2 |
| weekly | 3 | 9 | 9 | 0 | 1 | 0 | 1 | 0 | 0 | 1/1 |
| unusual_strength | 3 | 6 | 6 | 0 | 2 | 0 | 2 | 0 | 0 | 2/2 |
| eye_drop_od | 3 | 9 | 9 | 0 | 1 | 1 | 0 | 0 | 0 | 1/1 |
| long_list | 3 | 24 | 24 | 0 | 78 | 29 | 49 | 0 | 0 | 78/78 |
| control | 3 | 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 |

Run facts: {'model_calls': 60, 'resumed_from_disk': 0, 'duration_s_this_invocation': 1742.0}

