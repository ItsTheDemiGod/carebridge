# Plain-language explanation (Phase 3)

CareBridge explains and organises. It never diagnoses, never advises a dose change, and always tells the user to confirm with their doctor or pharmacist.

## Pipeline order (Phase 3e)
For each extracted advice, follow-up or warning line: (A) **phrase library**, exact match of the normalised line to a phrase or alias (`services/phrase_match.py`, `docs/PHRASE_LIBRARY.md`); matched lines show the library text in en/ta/hi and never reach the model; (B) otherwise the **local model path** below, with verification; (C) if verification fails, the **original English with a notice**. Near-misses (very similar but unequal wording) are reported for maintenance and never displayed.

## Provenance and labels
Every displayed text carries `provenance` (template, phrase_library, model_checked, original_only) and a computed `label_key`: `native_reviewed` (template or library text whose review_status is `reviewed`), `draft_unreviewed` (not yet reviewed), `machine_checked` (model-written, passed software checks only), `original_only`. A model-written line can never be `native_reviewed`. Authored English has no label. Label texts are templates `label.*`.

## Blind authoring
The phrase library (`phrases.json`) and the stress set (`eval/stress/stress_set.json`) were written from general knowledge of discharge wording only. No file under data/synthetic, data/ground_truth, data/rendered, eval/runs, eval/results, the data cache or docs/review_pack, no dev document, no earlier model output and not data/generate_synthetic.py was opened for that purpose. Coverage measured afterwards is therefore an honest dev-set number, though probably still optimistic (the generator uses common wording); real-world coverage is unmeasured.

## Pipeline (model path)
Input is the NORMALISED extraction (medicines with review_level / flags / readiness, follow-ups, red flags, advice). The live app has no document text, so nothing here reads it; evaluation may use it only for checking.

1. **Medicine lines: fixed templates, no model.** `services/templates.py` builds each line from structured fields using `data/templates/templates.json` (en / ta / hi). Human-reviewable, deterministic.
2. **Free-text lines: local model, text only.** Advice, follow-ups and warnings go through `services/narrative.py` (qwen3-vl:8b-instruct via Ollama, no images), batched per document per language, temperature 0, fixed seed.
   - Prompt A simplifies the extracted English. Prompt B translates the plain English into Tamil or Hindi. Prompt C back-translates Tamil/Hindi to literal English. Prompt D judges a candidate English text against the original.
3. **Verification** (`services/verification.py`). Deterministic checks first (ids, numbers, drug names, script, length, forbidden additions, urgency), then the judge. English: judge(plain English vs source). Tamil/Hindi: back-translate, then judge(back-translation vs source). A language text is **verified only if every deterministic check passes AND the judge says `supported`**.
4. **Assembly** (`services/explain.py`): disclaimer, medicines, follow-ups, advice, warnings, and a `not_found` section for missing items.

## Statuses
| field | values |
|---|---|
| line.status | `template` (fixed text), `verified` (all three languages verified), `unverified` (at least one language failed), `original_only` (no model text exists, e.g. the call failed) |
| LangText.status | same, per language |
| display_mode | `explanation` or `original_with_notice` (per language; the line value is a summary) |
| review_status | `draft_unreviewed` (every Tamil/Hindi string and every model-written line), `reviewed` (after the native-speaker import), `not_required` (English fixed text written by the authors) |

## Fallback rule
A language text that fails verification is NOT shown. The user sees the original extracted English text (`source_text`) with the fallback notice ("automatic explanation not available for this line; showing the original text"), in their language. English can verify while Tamil fails; each language falls back on its own. Unverified text is never presented as verified, and the number of warning lines always equals the number of extracted warnings (a failed warning still appears, as original text).

## Medicine rules
- Name as written in the quote; the resolved generic is shown only when present and different.
- A null strength or dose is never shown; the line says it was not found in the document.
- Every `must_confirm` medicine carries the confirm banner and a notice for each flag that has one.
- A medicine that is not `schedule_ready` is never described as settled (`settled=False`); weekly or other non-daily frequencies show the original text and ask the user to confirm.
- `unspecified` timing says no meal timing was found and to check the label or ask a pharmacist; it never implies any time is fine.
- An unknown enum value produces the "not found / check your document" line, never an error and never a guess.

## Out of scope
Explaining the diagnosis (the extraction schema has no diagnosis field), hospital course, interactions (Phase 4), reminders (Phase 6), PDF input, any language other than en/ta/hi, any real patient data.

## Limits
- The same local 8B model writes and judges, which weakens the judge (correlated blind spots). The deterministic checks do not share that weakness.
- Negation and urgency changes in Tamil/Hindi can only be caught by the back-translation judge; the deterministic checks cover numbers, drug names, script, length, forbidden phrases only where an English-script equivalent exists.
- Back-translation can hide a translation error (a wrong Tamil sentence can back-translate to a correct English one). Native review in Phase 7 is the real check on Tamil and Hindi.
- Tamil and Hindi template strings are drafts written without a native speaker.
- Dev set only, 20 synthetic documents, one model, one run per prompt version.
- Phase 3e dev numbers: the library covers 9 of 135 dev lines (6.7%); Hindi shown in Hindi 81%, Tamil 25% (Phase 3: 76% and 27%; the Tamil change is re-batching noise, not an effect of the library). The stress set (authored, 20+20 English pairs, 6+6 per Tamil/Hindi) gives false-reject 5% English, 50% Tamil, 17% Hindi and 95-100% combined detection; three false rejects come from the `you have` diagnosis regex firing on "if you have chest pain" while the judge said supported. See eval/results/stress-v1.
- `model_checked` is software-checked only; native review (Phase 7) is the real check.
