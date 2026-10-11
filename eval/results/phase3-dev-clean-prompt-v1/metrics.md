# phase3-dev-clean-prompt-v1

20 dev documents (clean condition), 135 free-text lines {'follow_up': 21, 'advice': 60, 'warning': 54}, 84 template medicine lines. Calls: 160 (5 failed). The same local 8B model writes and judges, which weakens the judge; native review in Phase 7 is the real check on Tamil and Hindi.

## Verified share (a language text is verified only if all deterministic checks pass AND the judge says supported)

| lang | all | advice | follow_up | warning | fallback rate |
|---|---|---|---|---|---|
| en | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| ta | 0.2 | 0.3 | 0.095 | 0.13 | 0.8 |
| hi | 0.696 | 0.8 | 0.714 | 0.574 | 0.304 |

Lines verified in all three languages: 0.156

## Failure reasons (first failing check or judge verdict)

- en: {}
- ta: {'judge:contradicts': 43, 'judge:omits_information': 29, 'no_model_text': 18, 'judge:adds_information': 11, 'forbidden_additions': 6, 'judge:unclear': 1}
- hi: {'judge:contradicts': 17, 'judge:omits_information': 14, 'judge:adds_information': 6, 'forbidden_additions': 2, 'script': 1, 'numbers': 1}

Deterministic checks failed (any, not only first): {'en': {}, 'ta': {'forbidden_additions': 6}, 'hi': {'script': 1, 'forbidden_additions': 2, 'numbers': 1}}

Judge verdicts: {'en': {'supported': 135}, 'ta': {None: 18, 'supported': 29, 'omits_information': 31, 'contradicts': 45, 'adds_information': 11, 'unclear': 1}, 'hi': {'supported': 97, 'omits_information': 14, 'contradicts': 18, 'adds_information': 6}}

## Latency per call type (s)

| type | n | median | p95 | max |
|---|---|---|---|---|
| simplify | 20 | 7.1 | 9.2 | 13.6 |
| translate | 40 | 15.1 | 103.2 | 199.9 |
| back | 40 | 7.0 | 8.6 | 8.9 |
| judge | 60 | 9.5 | 13.2 | 14.3 |

Total model time 2165 s, 207322 tokens.

## English readability (Flesch-Kincaid grade; heuristic, see eval/readability.py)

| set | lines | FK median | p25-p75 | pooled FK | mean sentence len | share words > 12 letters |
|---|---|---|---|---|---|---|
| source | 135 | 3.65 | 1.03 to 6.42 | 3.7 | 6.27 | 0.011 |
| plain_english_all | 135 | 2.88 | 0.8 to 4.96 | 2.89 | 6.67 | 0.008 |
| plain_english_verified | 135 | 2.88 | 0.8 to 4.96 | 2.89 | 6.67 | 0.008 |
