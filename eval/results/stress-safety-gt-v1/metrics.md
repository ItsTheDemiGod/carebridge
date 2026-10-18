# Safety stress set: ground-truth mode

documents: 30, model calls: 0. Counts only; interaction levels appear as per-category counts.

| category | docs | pairs checked | statuses | found by level | duplicates flagged / in ground truth |
|---|---|---|---|---|---|
| major_pair | 3 | 9 | {'interaction_found': 8, 'not_checked_no_record': 1} | {'major': 3, 'moderate': 2, 'minor': 0, 'unknown': 3} | 0 / 0 |
| moderate_pair | 3 | 9 | {'interaction_found': 5, 'not_checked_no_record': 4} | {'major': 0, 'moderate': 3, 'minor': 0, 'unknown': 2} | 0 / 0 |
| supplement_pair | 3 | 9 | {'interaction_found': 3, 'not_checked_no_record': 6} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 3} | 0 / 0 |
| duplicate | 3 | 6 | {'not_checked_no_record': 4, 'interaction_found': 2} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 2} | 3 / 3 |
| garbled_name | 3 | 9 | {'interaction_found': 2, 'not_checked_unconfirmed': 6, 'not_checked_no_record': 1} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 2} | 0 / 0 |
| weekly | 3 | 9 | {'not_checked_no_record': 2, 'not_checked_unconfirmed': 6, 'interaction_found': 1} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 1} | 0 / 0 |
| unusual_strength | 3 | 3 | {'not_checked_unconfirmed': 3} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 0} | 0 / 0 |
| eye_drop_od | 3 | 9 | {'not_checked_no_record': 2, 'not_checked_unconfirmed': 6, 'interaction_found': 1} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 1} | 0 / 0 |
| long_list | 3 | 84 | {'interaction_found': 78, 'not_checked_no_record': 6} | {'major': 2, 'moderate': 41, 'minor': 3, 'unknown': 32} | 0 / 0 |
| control | 3 | 15 | {'not_checked_no_record': 15} | {'major': 0, 'moderate': 0, 'minor': 0, 'unknown': 0} | 0 / 0 |

Invariant failures: 0
