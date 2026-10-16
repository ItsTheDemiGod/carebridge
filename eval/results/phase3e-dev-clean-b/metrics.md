# phase3e-dev-clean-b

20 dev documents (clean condition), 135 free-text lines {'follow_up': 21, 'advice': 60, 'warning': 54}. Phrase library active (pipeline: library, model with verification, original English). Calls: 160 (0 fresh, 0 failed), 1798 s.

**Coverage caveat.** Dev-set coverage is probably optimistic because the synthetic generator's wording is common wording; real-world coverage is unmeasured. The same 8B model writes, back-translates and judges, so `model_checked` means software-checked only, never human-reviewed.

## Share of lines by final provenance

| lang | kind | n | phrase_library | model_checked | original_only | shown in language | English fallback |
|---|---|---|---|---|---|---|---|
| en | all | 135 | 0.067 | 0.933 | 0.0 | 1.0 | 0.0 |
| en | advice | 60 | 0.15 | 0.85 | 0.0 | 1.0 | 0.0 |
| en | follow_up | 21 | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 |
| en | warning | 54 | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 |
| ta | all | 135 | 0.067 | 0.185 | 0.748 | 0.252 | 0.748 |
| ta | advice | 60 | 0.15 | 0.3 | 0.55 | 0.45 | 0.55 |
| ta | follow_up | 21 | 0.0 | 0.095 | 0.905 | 0.095 | 0.905 |
| ta | warning | 54 | 0.0 | 0.093 | 0.907 | 0.093 | 0.907 |
| hi | all | 135 | 0.067 | 0.741 | 0.193 | 0.807 | 0.193 |
| hi | advice | 60 | 0.15 | 0.8 | 0.05 | 0.95 | 0.05 |
| hi | follow_up | 21 | 0.0 | 0.81 | 0.19 | 0.81 | 0.19 |
| hi | warning | 54 | 0.0 | 0.648 | 0.352 | 0.648 | 0.352 |

## Comparison with Phase 3 (verified share, no library)

| lang | kind | Phase 3 | Phase 3e shown in language | change |
|---|---|---|---|---|
| en | all | 1.0 | 1.0 | +0.0 |
| en | advice | 1.0 | 1.0 | +0.0 |
| en | follow_up | 1.0 | 1.0 | +0.0 |
| en | warning | 1.0 | 1.0 | +0.0 |
| ta | all | 0.274 | 0.252 | -0.022 |
| ta | advice | 0.4 | 0.45 | +0.05 |
| ta | follow_up | 0.143 | 0.095 | -0.048 |
| ta | warning | 0.185 | 0.093 | -0.092 |
| hi | all | 0.763 | 0.807 | +0.044 |
| hi | advice | 0.867 | 0.95 | +0.083 |
| hi | follow_up | 0.762 | 0.81 | +0.048 |
| hi | warning | 0.648 | 0.648 | +0.0 |

## Library matches in the dev set

9 lines: ds_006/advice-3: Drink only boiled or filtered water.; ds_008/advice-2: Eat small, frequent meals.; ds_023/advice-0: Drink plenty of water.; ds_025/advice-2: Do not smoke.; ds_026/advice-2: Eat small, frequent meals.; ds_032/advice-0: Drink plenty of water.; ds_040/advice-2: Keep the wound clean and dry.; rx_003/advice-0: Drink plenty of water.; rx_017/advice-0: Drink plenty of water.

## Near-misses (reporting only, never displayed; 5 unmatched lines have one)

| count | ratio | dev line | closest library wording |
|---|---|---|---|
| 4 | 0.898 | drink plenty of warm fluids | Drink plenty of fluids. (adv.001) |
| 2 | 0.8 | walk for 30 minutes daily as tolerated | Walk for {n} minutes daily. (adv.024) |
| 1 | 0.809 | reduce salt in food | Reduce the salt in your food. (adv.011) |
| 1 | 0.82 | check blood sugar at home as advised | Check blood sugar at home. (adv.042) |
| 1 | 0.837 | redness, swelling or discharge from the wound | Watch for redness, swelling or discharge at the wound. (warn.033) |

## Most frequent unmatched lines (top 10)

- 4x avoid smoke, dust and strong smells
- 4x practise breathing exercises as taught
- 4x drink plenty of warm fluids
- 4x take rest and avoid smoke and dust
- 4x fever that does not settle
- 4x worsening breathlessness or chest pain
- 4x do not hold urine for long periods
- 3x worsening breathlessness
- 3x lips or fingers turning bluish
- 3x do deep breathing exercises as taught

## Library coverage on the stress-set sources (second estimate)

- realistic English sources: 4/55 (0.073)
- short translation sources: 6/12 (0.5); The short translation sources were written after the library and are biased towards it; the realistic sources are the second, independent estimate.
