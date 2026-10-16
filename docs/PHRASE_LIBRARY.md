# Phrase library (Phase 3e)

`data/templates/phrases.json`: 91 atomic, general phrases (44 advice, 34 warning, 13 follow-up) in English, Tamil and Hindi. Pipeline step A: a free-text line that EQUALS a phrase (or one of its up-to-4 aliases) is shown with the library text in all three languages and never goes to the model.

## Fields
`id` (adv./warn./fu.NNN), `kind`, `topic`, `english` (canonical), `english_aliases` (same meaning, general rewordings), `slot` (null or `{name: n, min, max}` for one integer written into the phrase, e.g. "after {n} days"), `ta` / `hi` (`text`, `review_status`), `urgent` (warnings only), `notes`.

## Rules (all enforced by `backend/tests/test_phrase_library.py`)
- No drug name (checked against the formulary), no dose or medicine word, no diagnosis, no reassurance, no instruction to start/stop/change a medicine, nothing that matches the forbidden-additions list.
- Ids and wordings are unique; every phrase has en/ta/hi; the `{n}` placeholder is identical in all three; digits are 0-9; no braces survive rendering; Tamil text is mostly Tamil script and Hindi mostly Devanagari.
- Every urgent warning carries an urgency cue in all aliases (English) and in Tamil and Hindi ("return to hospital" / "go to emergency immediately"); negations ("do not", "avoid", "does not") are present in Tamil and Hindi too.
- Tamil and Hindi are `draft_unreviewed` until the native-speaker import (`scripts/import_phrase_sheet.py`, see TRANSLATION_REVIEW.md). English is author-written (`not_required`).

## Strict matching (`services/phrase_match.py`)
Normalise (Unicode NFKC, lower case, collapse whitespace, strip bullets and edge punctuation), then require EXACT equality with the canonical wording or an alias, or equality with a slot wording where `{n}` is an integer without leading zero inside the phrase's range. No fuzzy matching, no model. A different number, unit, negation or symptom, or an extra clause, means no match and the line takes the model path.
`near_misses()` lists phrases that are at least 0.8 similar by `difflib` but not equal. It is used for REPORTING (what to add next) and is NEVER used for display.

## Authoring
Written blind: from general knowledge of how discharge instructions are worded. No file under `data/synthetic`, `data/ground_truth`, `data/rendered`, `eval/runs`, `eval/results`, the data cache or `docs/review_pack`, no dev document, no earlier model output and not `data/generate_synthetic.py` was opened for this purpose. Coverage measured afterwards is therefore an honest dev-set number (still probably optimistic, see EXPLANATION.md). The Tamil and Hindi were written by Claude Code, not by a native speaker.
