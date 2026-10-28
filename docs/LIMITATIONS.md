# Limitations of CareBridge (one list, plain language)

CareBridge is a college class prototype. It explains and organises a discharge summary or prescription; it is not medical advice, it is not clinically validated, and nothing here says it is accurate, reliable or safe. This page only collects, in one place, what the project's own documents already say it cannot do. Each statement links to its source; nothing in the source documents was changed to write this.

Read first: [`REVIEW_STATUS.md`](REVIEW_STATUS.md) (who has and has not checked what), [`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md) section 9 (what is not claimed), [`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 8.

## 1. Data
- All documents are synthetic. There is no real prescription or discharge summary anywhere in the project ([`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md) section 9; [`PRIVACY.md`](PRIVACY.md)).
- The development and held-out test documents come from the same generator and the same nine case templates, so they look alike. The held-out test is "never tuned on", not "different in kind" ([`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md); [`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 3).
- The medicine list (formulary) has 66 medicines. Names outside it cannot be identified and are only flagged; the formulary's Indian brand mappings are unverified and no pharmacist has checked it ([`FORMULARY_STATUS.md`](FORMULARY_STATUS.md); [`REVIEW_STATUS.md`](REVIEW_STATUS.md)).
- Because every synthetic medicine is in the formulary, name-accuracy figures are optimistic ([`NORMALISATION.md`](NORMALISATION.md)).
- The 30-prescription stress set was written by the project and renders use one font family and a simulated phone photo. A rendered, simulated photo is not a real photo ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) sections 1 and 6).

## 2. Extraction (reading the document)
- Raw model output was fully correct for only about a quarter of medicines; the rule layer repairs much of the rest, so the system leans on rules and on the user's confirmation ([`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md) section 11, items 1 and 2).
- A misreading whose quote agrees with itself cannot be seen by any rule, because the app holds no document text. Examples: an as-needed ("SOS") inhaler read as once daily (ds_035, official test, no flag); a name the model silently corrected in both the field and the quote (st_15 `photo`, stress set) ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 2 and 6; [`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 4.6).
- A dropped dosing token can leave only a "note" and still produce a schedule (ds_038: "PC" dropped; 2 of 285 schedule-ready medicines had a wrong schedule in the official test) ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 2; [`NORMALISATION.md`](NORMALISATION.md) limits).
- One name error was left unflagged in the official test (a whole line in the brand field, identity right) ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 2).
- About half of all medicines ask the user to confirm (406 of 795 in the official test; 95 of 208 in the stress renders) ([`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md); [`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 3). The model's output is not reproducible across Ollama versions: 2 of 5 dev documents gave identical normalised results after the update ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 1).
- The user must compare the extracted list with the paper document. A medicine that was never extracted cannot be warned about ([`SAFETY.md`](SAFETY.md) evaluation section).

## 3. Safety checks
- The interaction data (DDInter) is a partial download (groups A, B, D, H, L, P, R, V). Of 2,145 pairs among the 66 formulary medicines, 998 have a record; the rest are reported only as "not checked", which says nothing about safety ([`DDINTER_COVERAGE.md`](DDINTER_COVERAGE.md); [`SAFETY.md`](SAFETY.md)). In the stress set with perfect names, 41 of 162 pair cells had no record ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 5).
- The app says "an interaction was found" or "we could not check"; it never says "none" or "safe" ([`SAFETY.md`](SAFETY.md)).
- Many pairs are held back until the user confirms a medicine: in the stress set, 64 of 102 ground-truth pairs per render were not shown immediately; an unconfirmed pair is only an aggregated count line ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) sections 4.1 and 5). In the official test, 79 to 89 percent of pairs were "not checked" ([`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md) section 11, item 5).
- The 16-pair supplement is author-checked against official sources, not pharmacist-reviewed ([`REVIEW_STATUS.md`](REVIEW_STATUS.md); [`SAFETY.md`](SAFETY.md)).
- Not checked at all: drug-disease, drug-food, and therapeutic-class duplication. Duplicates are exact name matches only ([`SAFETY.md`](SAFETY.md) limits).
- Unusual strengths, weekly doses and "OD" eye drops are flagged and withheld, not interpreted ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) sections 4.3 to 4.5).
- The stress criteria passed on 30 authored documents; that is a check of designed cases, not a measure of how often they hold in use ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 6).

## 4. Translation and explanation
- Tamil and Hindi are machine-drafted and unreviewed by any native speaker; every Tamil and Hindi template string is `draft_unreviewed` ([`REVIEW_STATUS.md`](REVIEW_STATUS.md); [`EXPLANATION.md`](EXPLANATION.md)).
- For free-text lines, Tamil mostly falls back to the original English (46 of 255 lines verified in Tamil, 170 in Hindi, 239 in English in the official test) ([`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md) section 11, item 6; [`EXPLANATION.md`](EXPLANATION.md) fallback rule).
- The same model writes and judges the translation, so the check is weak ([`EXPLANATION.md`](EXPLANATION.md); [`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md)). Two Tamil calls truncated in the official run ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 6).
- The phrase library (91 phrases) covers few real lines (6.7 percent of dev lines) ([`PHRASE_LIBRARY.md`](PHRASE_LIBRARY.md)).

## 5. Statistics
- Small samples: 40 held-out documents (200 readings), 30 stress prescriptions (60 readings). Every interval is wide; the two renders of one document are not independent ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 4; [`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 3).
- Clustering by document makes plain Wilson intervals too narrow; the percentile bootstrap is unreliable for rare events such as 2 wrong schedules ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) sections 4 and 6).
- The dev set is 26 percent clean images and the test set 45 percent, so dev-versus-test differences partly reflect the mix, not the system ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 3).
- The stress run used Ollama 0.40.11 and the official run 0.40.5 (same model file), so the two are not directly comparable ([`STRESS_EXTRACTION_PROTOCOL.md`](STRESS_EXTRACTION_PROTOCOL.md) section 2).
- Some post-hoc breakdowns are descriptive only and are not official results ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md)).

## 6. What was not done
- The real-photo test (real phone pictures of printed prescriptions).
- The usability sessions with real people.
- Pharmacist review of the formulary and the interaction supplement; native-speaker review of Tamil and Hindi ([`REVIEW_STATUS.md`](REVIEW_STATUS.md)). The review packs are prepared, not sent.
- Clinical validation, and any regulatory work. The DPDP checklist is an engineering self-check, not legal advice and not reviewed by a lawyer ([`PRIVACY.md`](PRIVACY.md)).
- Phase 8 (deployment, demo, report) and Phase 9 (PWA, mobile app) ([`PHASE7_PLAN.md`](PHASE7_PLAN.md)).

## 7. Deployment
- The real flow runs only on the owner's computer, with a local Ollama model; user uploads are only ever sent to the localhost adapter ([`PRIVACY.md`](PRIVACY.md); [`API.md`](API.md)).
- The hosted demo, if any, is a pre-recorded walk-through of one synthetic dev document; it processes no photo and saves nothing ([`DEMO.md`](DEMO.md)).
- Processing takes roughly 30 to 60 s for extraction and longer for Tamil, on a consumer GPU ([`PROGRESS.md`](PROGRESS.md) Phase 6 and 7b).

## 8. Future-work ideas (ideas only; none applied, and the system stays frozen)
From the post-hoc review ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md) section 6):
- A second independent reading of dosing abbreviations from the image; never default an inhaler or other as-needed form to a daily schedule without confirmation.
- Treat a model-versus-rule timing conflict as a reason to require confirmation before a schedule is suggested (cost: more confirmation load).
- Flag a brand field that carries digits, units or a form prefix.
- Smaller chunks or a larger context for Tamil (needs a new freeze); stratified splits for any new evaluation; exact document-level bounds for rare counts.

From the stress review ([`STRESS_RESULTS.md`](STRESS_RESULTS.md) section 7):
- Do not require confirmation when identical brand and generic fields resolve exactly and appear in the quote, to cut the confirmation load (needs a new freeze and a new evaluation).
- A second independent reading of names from the image, to catch a silent correction of a garbled name.
- Pin the model server version for any further official run.
- Real-photo and usability testing, and the pharmacist and native-speaker reviews, before any claim beyond "class prototype".
