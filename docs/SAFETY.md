# Safety layer (Phase 4)

CareBridge explains and organizes. It never diagnoses, never recommends changing a dose, and always tells users to confirm with their doctor or pharmacist.

## What the interaction check can say
**An interaction was found, or we could not check. Nothing else.** The system never says a combination is safe, and never says "no interaction". This is a deliberate design choice: the DDInter download is partial (ATC groups A, B, D, H, L, P, R, V only), so the absence of a pair is uninformative. An ATC-letter "coverage rule" that would have let us say "covered, nothing listed" was tested and rejected (96 violations; see the addendum in `DDINTER_COVERAGE.md`).

| status | meaning | user sees |
|---|---|---|
| `interaction_found` | pair is in the DDInter-derived store (source `ddinter`) in the pharmacist-REVIEWED supplement (`curated_reviewed`) or in the author self-checked supplement (`curated_author_checked`); level major, moderate, minor or unknown | one line per pair, most severe first |
| `not_checked_no_record` | pair is in neither source. Says nothing about safety | one aggregated line with a count ("N medicine pairs could not be checked ... does not mean they are safe") |
| `not_checked_unconfirmed` | one or both medicines are not `interaction_ready` (name unresolved, garbled, flagged) | one aggregated line with a count asking to confirm the names |
| `not_checked_database_missing` | the derived store file is absent or unreadable | one line, no count; nothing crashes |

Per-pair detail stays in the `SafetyReport` data structure (`ExplanationDocument.safety`).

## Rules
- **Not found is never safe.**
- **Only `interaction_ready` medicines are checked.** `resolved_generic` comes from an exact printed formulary name, never from the model's generic field. Every other pair is `not_checked_unconfirmed`.
- **The supplement counts only when `reviewed` (a pharmacist; verdict not `remove`) or `author_checked` (prototype self-check by the project author with `checked_by`, `checked_on`, `basis` and evidence; NOT a pharmacist review).** Draft entries and incomplete author_checked entries are ignored; the engine reports how many it ignored. The supplement only holds documented interactions, never an entry saying "no interaction"; if both sources know a pair the higher level wins.
- Combination products are explicit in the formulary ("A + B"): each component is checked; the highest level wins. Names map through the formulary only (case-insensitive exact match), never fuzzy.
- Duplicates: the same resolved generic or the same printed name in more than one row gives a "possible double dose, please confirm" notice. Exact matches only; no class-level duplicate logic.
- `overall_state`: `confirm_first` if any medicine is must_confirm; else `review_interactions` if a major or moderate interaction was found; else `ok_to_review` (internal name; user text never says "ok" or "safe" about the result).
- Interaction lookup is a table lookup with no model.

## Guardrail (`app/safety/guardrails.py`)
Negation-aware scan of English text for three families: reassurance ("safe to take", "no risk", "you can take", "it is fine"), medicine/dose changes (stop, skip, increase, reduce, double, switch ... unless negated by "do not", "never"), diagnosis ("you have", "you are suffering from" unless in a conditional clause: if, when, whenever, unless, in case, up to three words before). An allow-list names the template ids whose fixed text legitimately contains a negated form. Tests scan every English template and every phrase-library entry and alias (all pass). At runtime it scans every model-written English line and the English back-translation of Tamil/Hindi lines (check `guardrail` in verification) and every assembled safety message; a hit fails closed (original text with notice; safety messages become the fallback notice) and is recorded. A family already present in the source line is not blamed on the model's rewrite.

## Evaluation (dev split, cached outputs, no model calls)
`eval/results/phase4-dev/`: 20 dev documents x 5 conditions plus the ground-truth medicine lists as reference.
- Ground truth: 148 medicine pairs, 96 with a DDInter interaction (major 0, moderate 21, minor 14, unknown 61).
- **Strict silent misses: 3.** All are in `poor` / ds_037: the model read Metformin as "Netfornin / Glibenclamide", and the evaluator could not match that garbled row to its ground-truth medicine. In the real engine that row is not `interaction_ready`, so its pairs are `not_checked_unconfirmed`. These come from the evaluator failing to match, not from the safety layer.
- **Silent misses not covered by a flag: 0** (must stay 0). A ground-truth interaction is covered only if each of its two medicines has an extracted row (matched, or assigned one-to-one from the unmatched not-ready rows) and the engine's pair status is `interaction_found` or `not_checked_unconfirmed`. The document-level banner is not used.
- Ground-truth medicines the extraction never saw: 0 in every condition in the dev set. **A medicine the extraction never saw cannot be warned about; the app depends on the user comparing the list with the document.**
- Downgrades to `not_checked_unconfirmed`: 328 ground-truth interactions (acceptable). The share of pairs not checked is high because many extracted rows need confirmation: 0.68 (text) to 0.89 (poor).
- False alarms 0; duplicates: the dev set has no duplicate medicines, so flagged 0 versus true 0 (the branch is unit-tested only).

## Licensing and attribution
Interaction data: DDInter (CC BY-NC-SA 4.0): attribution required, non-commercial, share-alike. The raw CSVs and the derived store (`data/reference/interactions_ddinter.json`) are gitignored and never committed; tests use tiny synthetic fixtures. The output shows an attribution line: with author_checked entries "Interaction data: DDInter (CC BY-NC-SA 4.0) plus a supplement drafted from official drug labels by the project author; not reviewed by a pharmacist (prototype)." (ta/hi drafts); otherwise the pharmacist-reviewed or waiting-for-review variant (English only). A notice says brand names are matched with a list not verified by a pharmacist. The supplement is drafted from official labels only (FDA, EMA); 11 of 16 entries apply a class-level statement to the pair (`basis: class_statement_applied`) and need the pharmacist to confirm class membership.

## Fail-safe behaviour
Store missing or unreadable: every pair is `not_checked_database_missing`, the user sees one line, nothing crashes. Supplement missing: treated as empty. Unknown generic: no record. Any guardrail hit: fail closed.

## Limits
The interaction data is incomplete and the app cannot tell which pairs are missing. DDInter levels are used; mechanism text is not. Therapeutic-class duplication, drug-disease and drug-food interactions are NOT checked. Tamil and Hindi safety strings are draft_unreviewed. The supplement is author self-checked (Phase 5c, 2026-10-16), not reviewed by a pharmacist; see docs/REVIEW_STATUS.md. Dev set only. The app is not medical advice.
