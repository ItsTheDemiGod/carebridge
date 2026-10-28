**POST-HOC (descriptive, done after the official run; not an official result; nothing in the system was changed in response).**

Pooled over the five conditions; medicine mentions = ground-truth medicines x 5 readings. Rates are ratios of sums (fully correct: matched medicines). Dev figures are recomputed from the cached dev raw outputs (`eval/runs/dev-ollama-v1`) with the same code as the test; the pooled dev values equal the committed ones (fully correct after rules 0.8115, brand name raw 0.6731). Cells with few documents are noisy: read the `docs` column.

### TEST split by difficulty

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 40 | 795 | 0.262 | 0.888 | 0.984 | 0.999 | 0.511 | 26 (1) | 0.495 |
| abbreviated | 11 | 225 | 0.302 | 0.782 | 0.987 | 1.000 | 0.422 | 8 (0) | 0.635 |
| clean | 16 | 355 | 0.251 | 0.966 | 0.986 | 0.997 | 0.623 | 12 (0) | 0.317 |
| messy | 13 | 215 | 0.238 | 0.870 | 0.977 | 1.000 | 0.419 | 6 (1) | 0.643 |

### TEST split by document type

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 40 | 795 | 0.262 | 0.888 | 0.984 | 0.999 | 0.511 | 26 (1) | 0.495 |
| discharge_summary | 26 | 520 | 0.237 | 0.873 | 0.983 | 0.998 | 0.517 | 23 (1) | 0.477 |
| prescription | 14 | 275 | 0.310 | 0.916 | 0.986 | 1.000 | 0.498 | 3 (0) | 0.528 |

### TEST split by case template

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 40 | 795 | 0.262 | 0.888 | 0.984 | 0.999 | 0.511 | 26 (1) | 0.495 |
| appendix | 4 | 80 | 0.392 | 0.988 | 0.988 | 1.000 | 0.550 | 0 (0) | 0.405 |
| cap | 4 | 80 | 0.237 | 0.875 | 0.950 | 1.000 | 0.338 | 4 (0) | 0.566 |
| cardiac | 5 | 150 | 0.273 | 0.967 | 1.000 | 1.000 | 0.540 | 2 (0) | 0.340 |
| copd | 3 | 90 | 0.211 | 0.789 | 1.000 | 1.000 | 0.667 | 3 (0) | 0.544 |
| dengue | 8 | 120 | 0.152 | 0.892 | 0.983 | 1.000 | 0.392 | 1 (0) | 0.669 |
| fracture | 1 | 20 | 0.050 | 0.550 | 1.000 | 1.000 | 0.850 | 1 (0) | 0.600 |
| gastro | 6 | 95 | 0.409 | 0.926 | 0.979 | 1.000 | 0.432 | 2 (1) | 0.602 |
| t2dm_htn | 6 | 120 | 0.276 | 0.866 | 0.967 | 0.992 | 0.533 | 12 (0) | 0.431 |
| uti | 3 | 40 | 0.175 | 0.775 | 1.000 | 1.000 | 0.625 | 1 (0) | 0.375 |

### DEV split by difficulty

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 20 | 420 | 0.307 | 0.811 | 0.983 | 0.998 | 0.462 | 14 (0) | 0.673 |
| abbreviated | 9 | 190 | 0.246 | 0.810 | 0.984 | 1.000 | 0.479 | 7 (0) | 0.706 |
| clean | 5 | 110 | 0.426 | 0.973 | 0.982 | 0.991 | 0.446 | 4 (0) | 0.537 |
| messy | 6 | 120 | 0.297 | 0.667 | 0.983 | 1.000 | 0.450 | 3 (0) | 0.746 |

### DEV split by document type

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 20 | 420 | 0.307 | 0.811 | 0.983 | 0.998 | 0.462 | 14 (0) | 0.673 |
| discharge_summary | 14 | 290 | 0.267 | 0.813 | 0.983 | 0.997 | 0.497 | 10 (0) | 0.642 |
| prescription | 6 | 130 | 0.398 | 0.808 | 0.985 | 1.000 | 0.385 | 4 (0) | 0.742 |

### DEV split by case template

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 20 | 420 | 0.307 | 0.811 | 0.983 | 0.998 | 0.462 | 14 (0) | 0.673 |
| appendix | 1 | 20 | 0.550 | 1.000 | 1.000 | 1.000 | 0.300 | 0 (0) | 0.600 |
| cap | 4 | 80 | 0.179 | 0.850 | 0.975 | 1.000 | 0.537 | 1 (0) | 0.577 |
| cardiac | 1 | 30 | 0.379 | 1.000 | 0.967 | 1.000 | 0.567 | 0 (0) | 0.414 |
| copd | 4 | 120 | 0.336 | 0.825 | 0.992 | 1.000 | 0.483 | 4 (0) | 0.798 |
| fracture | 3 | 60 | 0.237 | 0.567 | 0.983 | 1.000 | 0.533 | 2 (0) | 0.678 |
| gastro | 1 | 15 | 0.400 | 1.000 | 1.000 | 1.000 | 0.333 | 0 (0) | 0.667 |
| t2dm_htn | 2 | 40 | 0.436 | 0.923 | 0.975 | 0.975 | 0.400 | 4 (0) | 0.667 |
| uti | 4 | 55 | 0.259 | 0.691 | 0.982 | 1.000 | 0.309 | 3 (0) | 0.704 |

### Direct standardisation, dev versus test (difficulty strata)

Each split's stratum-specific rate (clean / abbreviated / messy) is reweighted to the OTHER split's stratum weights (the share of that metric's denominator in each stratum). Only difficulty is standardised; templates are too sparse (1 to 8 documents each).

Document mix: dev clean 5 / abbreviated 9 / messy 6; test clean 16 / abbreviated 11 / messy 13.

| metric | dev crude | test crude | crude gap (test - dev) | test reweighted to dev mix | gap vs dev | dev reweighted to test mix | gap vs test |
|---|---|---|---|---|---|---|---|
| fully correct, after rules | 0.811 | 0.888 | +0.076 | 0.855 | +0.044 | 0.844 | +0.044 |
| fully correct, raw | 0.307 | 0.262 | -0.045 | 0.270 | -0.037 | 0.340 | -0.078 |
| brand-name accuracy, raw | 0.673 | 0.495 | -0.178 | 0.554 | -0.119 | 0.641 | -0.146 |
| must_confirm share | 0.462 | 0.511 | +0.049 | 0.474 | +0.012 | 0.456 | +0.055 |
