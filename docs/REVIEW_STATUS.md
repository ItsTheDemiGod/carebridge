# Review status

**No independent human review (pharmacist or native speaker) has taken place.** CareBridge is a class prototype. The words "reviewed", "pharmacist" and "native speaker" appear in labels only where that really happened. Today it has not.

Wording for the project report (use exactly):
> Interaction supplement: author self-check against official sources, not independently reviewed. Formulary brand mappings: unverified. Tamil and Hindi: machine-drafted, unreviewed.

| Artifact | Status now | Who checked it, how | Upgrade path |
|---|---|---|---|
| Interaction supplement (`data/reference/interactions_supplement.json`, 16 pairs) | `author_checked` (all 16; source label `curated_author_checked`) | the project author (fixed string `author_prototype_selfcheck`), 2026-10-16, re-reading each official label or product information page; audit file `data/reference/review/interactions_supplement_selfcheck.csv` | a pharmacist returns `interactions_supplement_review.csv`; `python scripts/import_pharmacist_sheets.py FILE.csv` (normal mode) sets `reviewed` and needs initials and a date |
| Formulary (`data/reference/formulary.json`, 66 medicines) | `unverified_requires_pharmacist_review`; Indian brand mappings `unverified_prototype`; no row marked checked | name, route and some strengths compared with openFDA, WHO ATC, EMA and HPRA (`docs/FORMULARY_STATUS.md`) | pharmacist returns `formulary_review.csv` |
| Template sheets (`data/templates/review_sheet.csv` and the phase 4, 5, 5c "new" sheets) | every ta/hi string `draft_unreviewed`; English `not_required` | machine-drafted, software checks only | native speaker returns the sheet; `scripts/import_review_sheet.py` sets `reviewed` |
| Phrase library (`data/templates/phrases.json`, `phrase_review_sheet.csv`) | ta/hi `draft_unreviewed` | machine-drafted | native speaker returns the sheet; `scripts/import_phrase_sheet.py` |
| Review pack (`docs/review_pack/`, `send_to_reviewers/`) | prepared, not sent, no answers received | none | send to reviewers; import the returned files |
| Model-written Tamil/Hindi lines | `machine_checked` (software only) | back-translation and a same-model judge | never upgraded by software; only template or library text can become `native_reviewed` |

What the app tells users: the consent notice (v2) says it is a class prototype and not medical advice, that Tamil and Hindi are machine-drafted and unreviewed, and that the interaction information is limited, was drafted from official labels by the project author and is not pharmacist-reviewed. Interaction output says "may interact ... according to drug-label information collected by the project author (not checked by a pharmacist)". An English notice says brand names are matched to generic names with an unverified list.

Statuses: `draft_unreviewed` (disabled for interactions), `author_checked` (enabled, prototype), `reviewed` (enabled; only a real reviewer's returned sheet can set it).

**S11 (domperidone + levofloxacin):** the current UK SmPC on emc.medicines.org.uk was read as corroboration only; the evidence of record is HPRA and EMA. The exception to the regulator-domains-only network rule was accepted by the owner.
