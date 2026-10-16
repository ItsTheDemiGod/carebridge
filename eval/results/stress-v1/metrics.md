# stress-v1

Authored (blind) stress set; never shipped to users. Local model `qwen3-vl:8b-instruct`, text only. The same 8B model back-translates and judges, so the judge is weak evidence. Tamil/Hindi candidates were written by Claude Code and are NOT native-checked: they test whether the judge catches obvious faults and accepts clearly correct text, not translation quality. Small samples (6 correct and 6 wrong per Tamil/Hindi, 20 and 20 English): read the rates as rough.

## English

20 correct + 20 wrong candidates. **False-reject rate 0.05** (1/20; deterministic 1, judge 0; failing checks {'forbidden_additions': 1}). Overall accuracy 0.95. Judge unavailable: 0.

| wrong type | n | deterministic | judge | combined |
|---|---|---|---|---|
| clause_dropped | 3 | 0.0 | 1.0 | 1.0 |
| invented_advice | 3 | 0.0 | 1.0 | 1.0 |
| item_merged | 2 | 0.0 | 0.5 | 0.5 |
| negation_dropped_or_flipped | 3 | 0.0 | 1.0 | 1.0 |
| number_changed | 3 | 1.0 | 1.0 | 1.0 |
| timing_swapped | 2 | 0.0 | 1.0 | 1.0 |
| unit_changed | 2 | 0.0 | 1.0 | 1.0 |
| urgency_softened | 2 | 1.0 | 1.0 | 1.0 |
| **all wrong** | 20 | 0.25 | 0.95 | 0.95 |

Confusion (rows = truth, columns = system verdict):

| truth | verified | rejected |
|---|---|---|
| correct | 19 | 1 |
| wrong | 1 | 19 |

Missed (wrong but verified): en-w17 (item_merged)
False rejects: en-c13 (supported)

## Tamil (back-translation + judge)

6 correct + 6 wrong candidates. **False-reject rate 0.5** (3/6; deterministic 1, judge 2; failing checks {'forbidden_additions': 1}). Overall accuracy 0.75. Judge unavailable: 0.

| wrong type | n | deterministic | judge | combined |
|---|---|---|---|---|
| clause_dropped | 1 | 0.0 | 1.0 | 1.0 |
| invented_advice | 1 | 0.0 | 1.0 | 1.0 |
| negation_dropped_or_flipped | 1 | 0.0 | 1.0 | 1.0 |
| number_changed | 1 | 1.0 | 1.0 | 1.0 |
| timing_swapped | 1 | 0.0 | 1.0 | 1.0 |
| urgency_softened | 1 | 0.0 | 1.0 | 1.0 |
| **all wrong** | 6 | 0.167 | 1.0 | 1.0 |

Confusion (rows = truth, columns = system verdict):

| truth | verified | rejected |
|---|---|---|
| correct | 3 | 3 |
| wrong | 0 | 6 |

False rejects: ta-c2 (adds_information); ta-c3 (supported); ta-c6 (adds_information)

## Hindi (back-translation + judge)

6 correct + 6 wrong candidates. **False-reject rate 0.167** (1/6; deterministic 1, judge 0; failing checks {'forbidden_additions': 1}). Overall accuracy 0.917. Judge unavailable: 0.

| wrong type | n | deterministic | judge | combined |
|---|---|---|---|---|
| clause_dropped | 1 | 0.0 | 1.0 | 1.0 |
| invented_advice | 1 | 0.0 | 1.0 | 1.0 |
| negation_dropped_or_flipped | 1 | 0.0 | 1.0 | 1.0 |
| number_changed | 1 | 1.0 | 1.0 | 1.0 |
| timing_swapped | 1 | 0.0 | 1.0 | 1.0 |
| urgency_softened | 1 | 0.0 | 1.0 | 1.0 |
| **all wrong** | 6 | 0.167 | 1.0 | 1.0 |

Confusion (rows = truth, columns = system verdict):

| truth | verified | rejected |
|---|---|---|
| correct | 5 | 1 |
| wrong | 0 | 6 |

False rejects: hi-c3 (supported)

## English simplifier on harder lines (Prompt A, no reference answer)

15/15 lines produced. Unchanged: 0.0. Verified (deterministic + judge): 0.933.

| | FK median | FK pooled | mean sentence length | long-word share |
|---|---|---|---|---|
| source | 13.86 | 12.79 | 15.93 | 0.029 |
| simplified | 8.26 | 6.42 | 17.7 | 0.007 |

Lines where a fact appears lost or added (deterministic or judge): 1
- sm06: judge supported; deterministic ["forbidden_additions: phrases not in the source: ['diagnosis']"]

## Calls

| call type | calls | fresh | median s | max s |
|---|---|---|---|---|
| judge_en | 4 | 4 | 45.5 | 49.5 |
| back_ta | 3 | 3 | 9.3 | 9.7 |
| judge_ta | 2 | 2 | 19.8 | 20.3 |
| back_hi | 2 | 2 | 13.4 | 13.6 |
| judge_hi | 2 | 2 | 20.8 | 22.8 |
| simplify | 2 | 2 | 30.0 | 32.3 |
| judge_en(simplify) | 2 | 2 | 31.8 | 44.0 |

Total 17 calls (17 fresh), 0 failed, 439 s model time.
