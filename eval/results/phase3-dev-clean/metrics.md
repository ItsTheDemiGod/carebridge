# phase3-dev-clean

20 dev documents (clean condition), 135 free-text lines {'follow_up': 21, 'advice': 60, 'warning': 54}, 84 template medicine lines. Calls: 160 (0 failed). The same local 8B model writes and judges, which weakens the judge; native review in Phase 7 is the real check on Tamil and Hindi.

## Verified share (a language text is verified only if all deterministic checks pass AND the judge says supported)

| lang | all | advice | follow_up | warning | fallback rate |
|---|---|---|---|---|---|
| en | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| ta | 0.274 | 0.4 | 0.143 | 0.185 | 0.726 |
| hi | 0.763 | 0.867 | 0.762 | 0.648 | 0.237 |

Lines verified in all three languages: 0.237

## Failure reasons (first failing check or judge verdict)

- en: {}
- ta: {'judge:contradicts': 49, 'judge:omits_information': 34, 'forbidden_additions': 8, 'judge:adds_information': 6, 'numbers': 1}
- hi: {'judge:omits_information': 15, 'judge:adds_information': 9, 'judge:contradicts': 7, 'script': 1}

Deterministic checks failed (any, not only first): {'en': {}, 'ta': {'forbidden_additions': 9, 'numbers': 1}, 'hi': {'script': 1}}

Judge verdicts: {'en': {'supported': 135}, 'ta': {'adds_information': 7, 'omits_information': 40, 'supported': 38, 'contradicts': 50}, 'hi': {'supported': 104, 'omits_information': 15, 'adds_information': 9, 'contradicts': 7}}

## Latency per call type (s)

| type | n | median | p95 | max |
|---|---|---|---|---|
| simplify | 20 | 7.1 | 8.2 | 9.2 |
| translate | 40 | 13.9 | 34.9 | 35.7 |
| back | 40 | 6.9 | 8.9 | 9.2 |
| judge | 60 | 9.1 | 12.5 | 13.9 |

Total model time 1622 s, 221296 tokens.

## English readability (Flesch-Kincaid grade; heuristic, see eval/readability.py)

| set | lines | FK median | p25-p75 | pooled FK | mean sentence len | share words > 12 letters |
|---|---|---|---|---|---|---|
| source | 135 | 3.65 | 1.03 to 6.42 | 3.7 | 6.27 | 0.011 |
| plain_english_all | 135 | 2.88 | 0.8 to 5.23 | 3.01 | 6.61 | 0.008 |
| plain_english_verified | 135 | 2.88 | 0.8 to 5.23 | 3.01 | 6.61 | 0.008 |

## Corruption detection (known faults; deterministic alone / judge alone / combined)

Tamil/Hindi cover only number_changed, drug_name_swapped, wrong_script, item_dropped. Negation and urgency changes in Tamil/Hindi cannot be generated or checked deterministically and are NOT measured.

| lang/type | n | deterministic | judge | combined |
|---|---|---|---|---|
| en/clause_dropped | 40 | 0.075 | 1.0 | 1.0 |
| en/drug_name_swapped | 12 | 1.0 | 1.0 | 1.0 |
| en/invented_advice | 40 | 0.6 | 1.0 | 1.0 |
| en/negation_dropped | 40 | 0.0 | 1.0 | 1.0 |
| en/number_changed | 40 | 1.0 | 1.0 | 1.0 |
| en/timing_swapped | 8 | 0.0 | 1.0 | 1.0 |
| en/urgency_dropped | 8 | 1.0 | 1.0 | 1.0 |
| hi/number_changed | 19 | 1.0 | 1.0 | 1.0 |
| hi/wrong_script | 40 | 1.0 | 0.0 | 1.0 |
| ta/number_changed | 5 | 1.0 | 0.8 | 1.0 |
| ta/wrong_script | 37 | 1.0 | 0.0 | 1.0 |
| item_dropped (batch) | 135 | 1.0 | n/a | 1.0 |

False-reject rate on uncorrupted lines (source line as candidate): {'n': 135, 'deterministic': 0.0, 'judge': 0.0, 'combined': 0.0}
Model plain English rejected: {'n': 135, 'rejected': 0, 'note': 'includes real model errors, so it is not a false-reject rate'}
