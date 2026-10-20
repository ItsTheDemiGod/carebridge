# Final test results: final-test-v1

**OFFICIAL RUN (one-shot)**

Synthetic documents rendered by this project, held-out TEST split, one local model, protocol docs/FINAL_TEST_PROTOCOL.md. Proportions carry Wilson 95% intervals, F1 and fully-correct rates carry document-level bootstrap 95% intervals (2000 resamples, fixed seed); 40 documents give wide intervals.


## Coverage and latency

| condition | attempted | scored | skipped | skip reasons | latency median s | latency p95 s |
|---|---|---|---|---|---|---|
| text | 40 | 40 | 0 | - | 26.500 | 40.200 |
| clean | 40 | 40 | 0 | - | 28.700 | 41.800 |
| scan | 40 | 40 | 0 | - | 29.000 | 42.200 |
| photo | 40 | 40 | 0 | - | 28.900 | 42.000 |
| poor | 40 | 40 | 0 | - | 29.400 | 42.200 |
| all | 200 | 200 | 0 | - | 27.600 | 41.800 |

## Extraction, raw

| condition | docs | precision | recall | F1 (bootstrap) | fully correct (bootstrap) | hallucinated | invented-value rate |
|---|---|---|---|---|---|---|---|
| text | 40 | 0.969 [0.928, 0.987] | 0.969 [0.928, 0.987] | 0.969 [0.929, 1.000] | 0.208 [0.135, 0.280] | 5 | 0.357 [0.295, 0.423] |
| clean | 40 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.321 [0.234, 0.408] | 0 | 0.302 [0.245, 0.365] |
| scan | 40 | 0.987 [0.955, 0.997] | 0.987 [0.955, 0.997] | 0.987 [0.968, 1.000] | 0.306 [0.215, 0.402] | 2 | 0.298 [0.241, 0.362] |
| photo | 40 | 0.969 [0.928, 0.987] | 0.969 [0.928, 0.987] | 0.969 [0.934, 0.994] | 0.247 [0.163, 0.336] | 5 | 0.349 [0.288, 0.414] |
| poor | 40 | 0.994 [0.965, 0.999] | 0.994 [0.965, 0.999] | 0.994 [0.980, 1.000] | 0.228 [0.154, 0.314] | 1 | 0.339 [0.280, 0.404] |
| all | 200 | 0.984 [0.972, 0.990] | 0.984 [0.972, 0.990] | 0.984 [0.972, 0.993] | 0.262 [0.200, 0.328] | 13 | 0.329 [0.301, 0.357] |

Per-field accuracy (raw, pooled): strength 0.978 [0.966, 0.986]; form 0.992 [0.983, 0.997]; dose 0.955 [0.938, 0.968]; times_per_day 0.943 [0.924, 0.957]; timing_label 0.734 [0.702, 0.764]; is_prn 0.989 [0.978, 0.994]; duration_days 0.971 [0.956, 0.980]; brand_name 0.495 [0.460, 0.530]; generic_name 0.738 [0.706, 0.767]

Invented values by field (raw, pooled; of_null = fields the document leaves empty): strength: 7/15 (role confusion 0, in document 7, made up 0); dose: 0/0 (role confusion 0, in document 0, made up 0); times_per_day: 12/161 (role confusion 0, in document 12, made up 0); duration_days: 2/392 (role confusion 0, in document 2, made up 0); brand_name: 276/313 (role confusion 269, in document 1, made up 6); generic_name: 62/211 (role confusion 40, in document 2, made up 20)

## Extraction, normalised

| condition | docs | precision | recall | F1 (bootstrap) | fully correct (bootstrap) | hallucinated | invented-value rate |
|---|---|---|---|---|---|---|---|
| text | 40 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.937 [0.895, 0.974] | 0 | 0.022 [0.010, 0.052] |
| clean | 40 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.899 [0.839, 0.950] | 0 | 0.013 [0.005, 0.039] |
| scan | 40 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.887 [0.821, 0.940] | 0 | 0.018 [0.007, 0.045] |
| photo | 40 | 0.994 [0.965, 0.999] | 0.994 [0.965, 0.999] | 0.994 [0.980, 1.000] | 0.880 [0.819, 0.932] | 1 | 0.023 [0.010, 0.052] |
| poor | 40 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.837 [0.778, 0.892] | 0 | 0.032 [0.015, 0.064] |
| all | 200 | 0.999 [0.993, 1.000] | 0.999 [0.993, 1.000] | 0.999 [0.996, 1.000] | 0.888 [0.845, 0.927] | 1 | 0.022 [0.015, 0.032] |

Per-field accuracy (normalised, pooled): strength 0.979 [0.966, 0.987]; form 0.992 [0.984, 0.997]; dose 0.956 [0.939, 0.968]; times_per_day 0.989 [0.979, 0.994]; timing_label 0.990 [0.980, 0.995]; is_prn 0.991 [0.982, 0.996]; duration_days 0.998 [0.991, 0.999]; brand_name 0.979 [0.966, 0.987]; generic_name 0.985 [0.974, 0.991]

Invented values by field (normalised, pooled; of_null = fields the document leaves empty): strength: 7/15 (role confusion 0, in document 7, made up 0); dose: 0/0 (role confusion 0, in document 0, made up 0); times_per_day: 7/165 (role confusion 0, in document 7, made up 0); duration_days: 2/399 (role confusion 0, in document 2, made up 0); brand_name: 5/314 (role confusion 0, in document 1, made up 4); generic_name: 3/215 (role confusion 0, in document 0, made up 3)

## Flags, names and readiness (app mode)

| condition | medicines | must_confirm (CI) | name errors remaining | unflagged | timing errors | unflagged | interaction_ready | WRONG resolved_generic | schedule_ready | wrong schedule |
|---|---|---|---|---|---|---|---|---|---|---|
| text | 159 | 76 (0.478 [0.402, 0.555]) | 1 | 1 | 1 | 0 | 83 | 0 | 61 | 0 |
| clean | 159 | 76 (0.478 [0.402, 0.555]) | 2 | 0 | 2 | 0 | 83 | 0 | 60 | 0 |
| scan | 159 | 74 (0.465 [0.390, 0.543]) | 4 | 0 | 2 | 1 | 85 | 0 | 64 | 2 |
| photo | 159 | 87 (0.547 [0.470, 0.623]) | 7 | 0 | 2 | 0 | 72 | 0 | 54 | 0 |
| poor | 159 | 93 (0.585 [0.507, 0.659]) | 12 | 0 | 1 | 0 | 66 | 0 | 46 | 0 |
| all | 795 | 406 (0.511 [0.476, 0.545]) | 26 | 1 | 8 | 1 | 389 | 0 | 285 | 2 |

## Safety engine (aggregated counts; no pair-level interaction levels are published)

- strict silent misses: 3 (covered by a confirmation flag: 3; NOT covered: 0)
- downgrades to not_checked_unconfirmed: 753; false alarms: 0
- pairs per condition: {'text': 262, 'clean': 262, 'scan': 262, 'photo': 262, 'poor': 262}; share not checked: {'text': 0.844, 'clean': 0.79, 'scan': 0.794, 'photo': 0.851, 'poor': 0.885}
- duplicates: {'flagged': 0, 'true_flagged': 0, 'false_flagged': 0, 'ground_truth_duplicates': 0}

## Explanation pipeline (clean condition)

- documents 40, lines 255, by kind {'follow_up': 42, 'advice': 118, 'warning': 95}
- verified share (Phase 3 definition): {'en': {'all': 0.937, 'advice': 0.873, 'follow_up': 0.976, 'warning': 1.0}, 'ta': {'all': 0.18, 'advice': 0.254, 'follow_up': 0.286, 'warning': 0.042}, 'hi': {'all': 0.667, 'advice': 0.754, 'follow_up': 0.762, 'warning': 0.516}}
- provenance and label distribution per language: {'en': {'all': {'n': 255, 'phrase_library': 0.059, 'model_checked': 0.937, 'original_only': 0.004, 'shown_in_language': 0.996, 'english_fallback': 0.004}, 'advice': {'n': 118, 'phrase_library': 0.127, 'model_checked': 0.873, 'original_only': 0.0, 'shown_in_language': 1.0, 'english_fallback': 0.0}, 'follow_up': {'n': 42, 'phrase_library': 0.0, 'model_checked': 0.976, 'original_only': 0.024, 'shown_in_language': 0.976, 'english_fallback': 0.024}, 'warning': {'n': 95, 'phrase_library': 0.0, 'model_checked': 1.0, 'original_only': 0.0, 'shown_in_language': 1.0, 'english_fallback': 0.0}}, 'ta': {'all': {'n': 255, 'phrase_library': 0.059, 'model_checked': 0.18, 'original_only': 0.761, 'shown_in_language': 0.239, 'english_fallback': 0.761}, 'advice': {'n': 118, 'phrase_library': 0.127, 'model_checked': 0.254, 'original_only': 0.619, 'shown_in_language': 0.381, 'english_fallback': 0.619}, 'follow_up': {'n': 42, 'phrase_library': 0.0, 'model_checked': 0.286, 'original_only': 0.714, 'shown_in_language': 0.286, 'english_fallback': 0.714}, 'warning': {'n': 95, 'phrase_library': 0.0, 'model_checked': 0.042, 'original_only': 0.958, 'shown_in_language': 0.042, 'english_fallback': 0.958}}, 'hi': {'all': {'n': 255, 'phrase_library': 0.059, 'model_checked': 0.667, 'original_only': 0.275, 'shown_in_language': 0.725, 'english_fallback': 0.275}, 'advice': {'n': 118, 'phrase_library': 0.127, 'model_checked': 0.754, 'original_only': 0.119, 'shown_in_language': 0.881, 'english_fallback': 0.119}, 'follow_up': {'n': 42, 'phrase_library': 0.0, 'model_checked': 0.762, 'original_only': 0.238, 'shown_in_language': 0.762, 'english_fallback': 0.238}, 'warning': {'n': 95, 'phrase_library': 0.0, 'model_checked': 0.516, 'original_only': 0.484, 'shown_in_language': 0.516, 'english_fallback': 0.484}}}

## Dev versus test (dev = committed dev results; expected higher on dev, see protocol section 4)

| metric | dev | test | test minus dev |
|---|---|---|---|
| medicine F1, raw | 0.983 | 0.984 | 0.000 |
| fully-correct medicine rate, raw | 0.307 | 0.262 | -0.045 |
| invented-value rate, raw | 0.286 | 0.329 | 0.043 |
| timing label field, raw | 0.729 | 0.734 | 0.005 |
| brand name field, raw | 0.673 | 0.495 | -0.178 |
| medicine F1, normalised | 0.998 | 0.999 | 0.001 |
| fully-correct medicine rate, normalised | 0.811 | 0.888 | 0.076 |
| invented-value rate, normalised | 0.056 | 0.022 | -0.035 |
| timing label field, normalised | 0.991 | 0.990 | -0.001 |
| brand name field, normalised | 0.979 | 0.979 | 0.000 |
| share of medicines at must_confirm | 0.462 | 0.511 | 0.049 |
| name errors remaining, unflagged | 0 | 1 | 1 |
| wrong resolved_generic among interaction_ready | 0 | 0 | 0 |
| silent misses, strict | 3 | 3 | 0 |
| silent misses not covered by a flag | 0 | 0 | 0 |
| false alarms | 0 | 0 | 0 |
| share of free-text lines shown in en | 1.000 | 0.996 | -0.004 |
| share of free-text lines shown in ta | 0.252 | 0.239 | -0.013 |
| share of free-text lines shown in hi | 0.807 | 0.725 | -0.082 |
