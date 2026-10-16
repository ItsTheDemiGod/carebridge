# Confirm-first layer (Phase 5)

CareBridge explains and organises. It never diagnoses, never recommends changing a dose, and always tells users to confirm with their doctor or pharmacist. This layer lets the **user** resolve what the software could not: medicine names it could not match, and details it could not read with confidence. It is an **overlay** on the normalised document; the normalisation code and the safety engine are unchanged.

Code: `app/services/confirmation.py` (pure `apply(normalised, confirmations) -> Overlay`), `app/schemas/confirmation.py`, routes in `app/api/routes_review.py`. Tests: `tests/test_confirmation.py` (including the property-style test), `tests/test_api_review.py`.

## Flow
1. `GET /documents/{id}/medicines`: every extracted medicine with its source quote, reasons (template id + text in the session language), readiness and allowed actions.
2. The user decides per medicine and `POST /documents/{id}/confirmations` sends the **whole** set (it replaces the previous set; an empty set clears it).
3. `GET /documents/{id}/result` assembles the explanation from the **overlay** (see `API.md`). Before any confirmation it uses the unconfirmed normalised document.

## Decisions (per extracted medicine, by index; one action each)
| action | meaning | extra fields |
|---|---|---|
| `confirm_as_extracted` | "this matches my document" | optional `schedule_edit`, `acknowledged_flags` |
| `select_formulary_drug` | "this is the right medicine" (from the picker) | `formulary_id`, `strength_choice` (one of the entry's strengths or `as_on_my_label`), optional `schedule_edit`, `acknowledged_flags` |
| `not_in_list` | "my medicine is not in the list" | optional `note` (at most 80 characters, stored, never used for any lookup) |
| `remove` | "this is not on my document" | none |

Also `added_medicines[]` (max 10): `{formulary_id, strength_choice, dose, schedule}` where `dose` is one of a fixed list (`1/2 tablet`, `1 tablet`, ... `1 application`) and `schedule` is `{times_per_day 1-6 | as_needed, timing_label, duration_days | null}`. There is no free-text medicine. Models reject unknown fields (`extra=forbid`).

## Rules (enforced on the server and tested)
1. **interaction_ready** only with a formulary identity (an exact printed-name match from normalisation, or a formulary entry the user selected, provenance `user_selected`) **and** every `must_confirm` reason resolved.
   - Name-related reasons (`unresolved_name`, `near_miss_name`, `role_corrected`, `duplicate_name_fields`, `name_not_in_quote`, and, stricter than the brief, `missing_name`, `multiple_drugs_in_quote`, `possible_combination`) are resolved only by `select_formulary_drug`, or by `confirm_as_extracted` on a medicine that already has an exact formulary identity. An acknowledgement alone never identifies a medicine.
   - Every other reason (`incomplete_quote`, `unusual_strength`, `non_daily_frequency`, `ambiguous_OD`, `conflicting_*`, `low_confidence`, `quote_not_in_document`, any future flag) needs its id in `acknowledged_flags`. An id that is not one of that medicine's reasons is rejected (`422 invalid_confirmation`). A missing acknowledgement leaves the medicine `must_confirm`.
2. `confirm_as_extracted` on a medicine **without** a formulary identity keeps it not interaction_ready (`not_checked_reason: not_identifiable`). `not_in_list` also drops the extracted identity (so no lookup or duplicate check can use it) and reports `user_not_in_list`. User free text is never used for lookup and never makes a medicine checkable.
3. **schedule_ready** only if there is no unresolved reason, the frequency is daily and known (`times_per_day` and `timing_label` from rules, from a user `schedule_edit`), not PRN and not `as_needed`. `non_daily_frequency` medicines are **never** schedule_ready in this version, even after identification, acknowledgement and a schedule edit. `unspecified` timing counts as known (no meal timing was written).
4. **Provenance** is recorded on every changed field (`rule`, `model`, `formulary`, `user_selected`, `user_confirmed`, `user_added`) in `ConfirmedMedicine.provenance`. An audit trail (`decisions` payload, encrypted) keeps action, time and whether a note exists (not the note).
5. The overlay is a **copy**: removed medicines are absent (so absent from every pair result), added ones are appended. The unchanged safety engine runs on the overlay. The explanation shows "you confirmed this" labels (templates `confirm.*`) beside user-resolved items.
6. Added medicines come only from the formulary picker.

## Requirement for Phase 6 (UI) and residual risk
- **The picker must show brand names, the generic name and the strength next to the medicine's source quote** (`picker.compare_note`: "Compare the brand name, generic name and strength with your document before you choose.") and require an explicit selection. Do not preselect a suggestion.
- The user's selection is the user's **own attestation**. If the user selects the wrong drug, the interaction results and the schedule are for the wrong drug, and the software cannot detect it. This residual risk is accepted and is the reason the result always keeps the document's own text, the disclaimer, and "we could not check" wording for everything not looked up.
- The formulary has 66 drugs and is **unverified until a pharmacist reviews it**; a medicine outside it cannot be selected, only reported as `not_in_list` (never checked).
- "Removed" is an assertion by the user that the software read something that is not on the document; the software cannot verify it either.
- Tamil and Hindi strings of this screen are drafts until native review (`data/templates/review_sheet_phase5_new.csv`).

## Not done in this phase
No UI; no learning from user selections; no free-text matching; no editing of strengths outside the formulary list (use `as_on_my_label` and the source quote).
