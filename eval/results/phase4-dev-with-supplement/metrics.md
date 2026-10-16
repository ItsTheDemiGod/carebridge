# Phase 4 safety evaluation (dev-ollama-v1, dev split)

No model calls. 20 dev documents x 5 conditions (cached extractions, normalisation v2, app mode). Store available: True. Supplement: 16 reviewed entries used, 0 ignored (not reviewed).

## Pair statuses by condition (extraction-based; duplicate-medicine pairs excluded)

| condition | docs | pairs | interaction_found | not_checked_no_record | not_checked_unconfirmed | not_checked_database_missing | share not checked |
|---|---|---|---|---|---|---|---|
| text | 20 | 148 | 48 | 23 | 77 | 0 | 0.676 |
| clean | 20 | 148 | 40 | 13 | 95 | 0 | 0.73 |
| scan | 20 | 148 | 26 | 9 | 113 | 0 | 0.824 |
| photo | 20 | 148 | 19 | 7 | 122 | 0 | 0.872 |
| poor | 20 | 148 | 16 | 9 | 123 | 0 | 0.892 |

## Ground truth (reference; every medicine treated as interaction_ready)

148 medicine pairs in 20 documents; statuses {'interaction_found': 96, 'not_checked_no_record': 52}; interactions found by level {'major': 0, 'moderate': 21, 'minor': 14, 'unknown': 61}.

## Safety metrics (extraction-based vs ground truth, per pair)

| metric | count |
|---|---|
| silent misses, STRICT (per-pair name matching only) | 3 |
| silent misses NOT covered by a flag (must be 0) | 0 |
| downgrades to not_checked_unconfirmed (acceptable) | 328 |
| false alarms | 0 |
| level mismatches among found | 0 |

Downgrade causes (flags on the unconfirmed medicine): {'duplicate_name_fields': 74, 'near_miss_name': 120, 'conflict_timing_label': 87, 'role_corrected': 119, 'conflict_duration_days': 3, 'incomplete_quote': 38, 'unusual_strength': 26, 'name_not_in_quote': 58, 'unresolved_name': 10, 'conflict_times_per_day': 7}

The strict count comes from the evaluator failing to match a garbled extracted row (for example Netfornin/Glibenclamide for Metformin) to its ground-truth medicine; in the real engine that row is not interaction_ready and its pairs are not_checked_unconfirmed. A ground-truth interaction counts as covered only if both of its medicines have an extracted row (matched, or assigned one-to-one from the unmatched not-ready rows) and the engine pair status is interaction_found or not_checked_unconfirmed. The document-level banner is NOT used.

Ground-truth medicines the extraction never saw (no extracted row), and the ground-truth interactions they affect:

| condition | medicines missed entirely | interactions affected |
|---|---|---|
| text | 0 | 0 |
| clean | 0 | 0 |
| scan | 0 | 0 |
| photo | 0 | 0 |
| poor | 0 | 0 |
A medicine the extraction never saw cannot be warned about; the app depends on the user comparing the list with the document.


STRICT SILENT MISS CASES (covered_by_flag says whether the per-pair rule covers them):
```
[
 {
  "cond": "poor",
  "doc": "ds_037",
  "gt": [
   "Metformin",
   "Glimepiride"
  ],
  "gt_level": "moderate",
  "why": "no entry (a medicine was not extracted or not matched)",
  "covered_by_flag": true
 },
 {
  "cond": "poor",
  "doc": "ds_037",
  "gt": [
   "Metformin",
   "Telmisartan"
  ],
  "gt_level": "unknown",
  "why": "no entry (a medicine was not extracted or not matched)",
  "covered_by_flag": true
 },
 {
  "cond": "poor",
  "doc": "ds_037",
  "gt": [
   "Metformin",
   "Atorvastatin"
  ],
  "gt_level": "unknown",
  "why": "no entry (a medicine was not extracted or not matched)",
  "covered_by_flag": true
 }
]
```

## Duplicates

Ground-truth duplicate groups: 0. Flagged: 0 (true 0, false 0). Missed: 0.

## overall_state by condition

| condition | confirm_first | review_interactions | ok_to_review | confirm_first share |
|---|---|---|---|---|
| text | 15 | 2 | 3 | 0.75 |
| clean | 18 | 1 | 1 | 0.9 |
| scan | 17 | 2 | 1 | 0.85 |
| photo | 20 | 0 | 0 | 1.0 |
| poor | 17 | 1 | 2 | 0.85 |

Share of documents showing the confirm_first banner (all conditions): 0.87.

Supplement: if all 16 drafted entries became reviewed, 0 of the 2,145 formulary pairs would change from not_checked_no_record to interaction_found.
