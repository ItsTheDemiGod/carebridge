# Decisions

- **FastAPI + pytest backend**: async-friendly, automatic validation/docs, easy to test with TestClient.
- **React + Vite + TypeScript frontend**: fast dev loop, typed UI code; Vite proxy avoids CORS during dev.
- **Tailwind CSS v4 via @tailwindcss/vite**: current default for new projects; no config file needed. Custom palette/tokens will be CSS variables in Phase 6.
- **Python 3.12 venv**: 3.11 not installed locally; 3.12 is compatible with the stack.
- **pydantic-settings for config**: typed env-var loading; API key optional until LLM phases.
- **pytest.ini sets `pythonpath = .`**: lets `pytest` import `app` from `backend/`.
- **Gemini API for LLM calls** (replaced the earlier Claude API plan in Phase 2): free tier suits a student project. See the Phase 2 entries below.
- **Storage (Postgres vs SQLite) deferred to Phase 5**: not needed until persistence exists.
- **GSAP and tsParticles deferred**: installed in Phase 6 when design work begins, per instruction.
- **Spans recorded at build time**: the generator's text buffer records offsets as it appends strings, then asserts text[start:end] equals the span. Never typed by hand; the validator re-checks.
- **Ground truth conventions**: names, duration_text, abbreviations kept as written (so extraction is not rewarded for normalising); strength, dose and numeric frequency fields normalised.
- **`.gitattributes` LF for data files**: Windows autocrlf would shift offsets.
- **Dev/test split fixed in manifest.json**: 20 dev / 40 test; test is never used for tuning (rule in CLAUDE.md).
- **Prescriptions give chronic medicines a 30-day duration; discharge summaries leave them open-ended**: matches common practice and adds variety.
- **Interaction data: DDInter + own formulary mapping** (see docs/DRUG_DATABASE_RECOMMENDATION.md). RxNav interaction API was discontinued 2 Jan 2024; DrugBank academic downloads are paused.
- **Interaction checks are table lookups, never LLM memory**; an unlisted pair means "not checked", not "safe".

## Phase 2
- **Model: `gemini-3.8-flash`** (checked 2026-10-04). Reasons: Flash-class, listed as Stable (not preview), accepts text/image/PDF, supports structured output, free tier for input and output. Sources: https://ai.google.dev/gemini-api/docs/models (3.8, 3.7, 3.6, 3.5 Flash all Stable; 3 Flash is preview; 2.5 Flash is limited access), https://ai.google.dev/gemini-api/docs/pricing (3.8 Flash: free tier yes; paid $0.75 / $3.75 per 1M tokens in/out until 2026-12-31).
- **Free-tier limits NOT published in the docs**: https://ai.google.dev/gemini-api/docs/rate-limits says limits depend on usage tier and "can be viewed in Google AI Studio" (https://aistudio.google.com/rate-limit). The numbers (RPM, TPM, RPD) therefore could not be recorded here; check them in AI Studio. Default `GEMINI_MAX_REQUESTS_PER_MINUTE=5` is a conservative guess, not a documented limit.
- **Privacy**: free tier may let Google use content for product improvement and human review, so only synthetic documents are ever sent. Enforced in code by `app/services/guards.py` (path must be inside data/synthetic or data/rendered), unit-tested.
- **Test-split guard**: any extraction or evaluation on the test split needs `--final-test-run` and is appended to `eval/test_runs.log`.
- **Extraction output schema** (`extraction_output.py`): offsets replaced by `source_quote`, plus `confidence` and `unreadable_parts`. Gemini accepted the Pydantic schema as-is via `response_schema`; no simplification was needed.
- **Own retry/backoff instead of the SDK's**: needed to honour RetryInfo hints, enforce requests per minute, and stop early on daily-quota errors (waiting a minute cannot fix those).
- **Keep a reference to the genai Client**: a temporary client is closed when garbage-collected and the call fails with "client has been closed".
- **`unspecified` timing label**: used when a frequency is stated but no time of day or meal relation is given; `other` is kept for genuinely unusual instructions (the generator no longer emits it).
- **Patient names drawn from an independent RNG** (seeded per document id); the old name draws are still consumed from the main RNG so every other part of every document is unchanged (tested against the Phase 1 commit).
- **Renders**: PNG outputs for all conditions (JPEG compression applied in memory, then saved as PNG); PDFs for clean and scan use fixed creation dates so files are byte-identical across runs.

## Phase 2 (continued): local Ollama provider (checked 2026-10-09)
- **Why**: Gemini free tier allows about 20 requests/day; billing is not an option. Extraction runs locally on an RTX 4060 (8 GB) via Ollama 0.35.1. Gemini stays an optional provider for comparison.
- **API facts** (https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md, https://docs.ollama.com/capabilities/thinking): images go in `messages[].images` as base64 strings; `format` takes a JSON schema object for structured output; options `temperature`, `seed`, `num_ctx`, `num_predict`; `keep_alive` is a top-level request field (default 5m); `think: false` requests no thinking, reasoning appears in `message.thinking`, the answer in `message.content`; response gives `prompt_eval_count`, `eval_count`, `done_reason`.
- **Observed**: with tag `qwen3-vl:8b`, `think:false` was IGNORED in a local test (response had empty `content` and a `<think>` block in `message.thinking`, 2026-10-09). So the default tag is the thinking variant.
- **Tags** (https://ollama.com/library/qwen3-vl/tags): `qwen3-vl:8b-instruct` and `qwen3-vl:8b-thinking` both exist, 6.1 GB each, same 8B size and q4_K_M quantisation. Plan: use `qwen3-vl:8b-instruct` (non-thinking, same parameter size) once pulled.
- **Env vars** (https://docs.ollama.com/faq): `OLLAMA_FLASH_ATTENTION=1` enables flash attention (less memory as context grows). `OLLAMA_KV_CACHE_TYPE` = f16 (default) | q8_0 (about 1/2 KV memory, very small precision loss) | q4_0 (about 1/4, small-medium loss); needs flash attention; global for all models. Recommendation for 8 GB: flash attention on plus q8_0, to fit a larger context fully on GPU. Not measured yet; awaiting user to set them.
- **Privacy**: Ollama adapter refuses any base URL whose host is not localhost/127.0.0.1.
- **Model switch to `qwen3-vl:8b-instruct`** (2026-10-09): the default `qwen3-vl:8b` tag is the thinking variant and ignored `think:false`. The instruct tag has the same size (8B, q4_K_M, 6.1 GB), so it is the `OLLAMA_MODEL` default. The old tag stays installed. Flash attention and q8_0 KV cache are now set by the user. GPU split of the instruct tag: 6144 ctx = 9%/91% CPU/GPU (6.1 GB); 8192 ctx = 11%/89% (6.3 GB).
- **Provider abstraction** (`app/llm/`): `base.py` (Part, LLMResponse, LLMError, Provider), `gemini.py` (moved unchanged: throttle, backoff, quota detection), `ollama.py`. The interface takes the Pydantic output model rather than a raw JSON schema; each adapter derives what it needs. Failures are `LLMError(reason)`; the service turns them into `ExtractionResult(skipped=True, error=reason)` so the evaluator reports them instead of scoring them. Usage is normalised to `prompt_tokens/output_tokens/total_tokens`.
- **Ollama safety checks**: base URL must be localhost/127.0.0.1; `context_truncated` if `done_reason=length` or prompt+generated tokens reach `num_ctx`; `image_not_received` if an image call has fewer than `OLLAMA_MIN_IMAGE_PROMPT_TOKENS` (1200, to be calibrated) prompt tokens. Cached prompt tokens (`prompt_eval_cached_count`) are added to the prompt count. PDFs return `unsupported_input`.
- **Cache key** = file bytes + provider tag (provider, model, num_ctx, image side cap, seed) + prompt version + schema version.
- **Schema sent to Ollama**: unmodified Pydantic JSON schema so far; will be simplified only if Step 4 shows Ollama mishandles it.
- **Wire schema for Ollama**: the JSON schema sent in `format` is the Pydantic schema with every object property marked `required` (`require_all`). Reason: with Pydantic's default (only `document_type` required) the model answered with no medications. `$defs`/`$ref`, enums and nullable `anyOf` were accepted as-is. Pydantic validation on our side is unchanged. Included in the cache tag (`wire-required-all`).
- **Prompt choice**: v1 kept as default after v2/v3 (see docs/PROMPT_LOG.md).
- **No Gemini baseline**: the earlier Gemini dev run was incomplete; comparison would need a quota-limited rerun.

## Phase 2h
- **Fix in code, not in the prompt**: two prompt revisions failed, so timing/frequency/duration and name roles are derived after extraction by deterministic rules (docs/NORMALISATION.md). The rule value is final when it derives something; disagreements are kept as `conflict_*` flags.
- **Fuzzy name threshold 0.92**: above the most confusable formulary pair (omeprazole/esomeprazole 0.91), so a fuzzy match cannot land on another drug; fuzzy matches are always flagged `near_miss_name`.
- **Evaluation pairs a medicine if raw OR normalised names match**, so normalisation cannot improve F1 by hiding a medicine or lose it by dropping a name.
- **Audit-only flags** (`conflict_*`, `role_corrected`) do not raise `needs_verification` after the Step 6 revision (255/420 flagged before, 133/420 after).

## Phase 2i
- **Ground truth for strength is correct**: the generator deliberately omits strength in some messy documents (and labels null); the model filled the gap from the dose or a neighbouring line. No change to data.
- **Quote check threshold 0.95 plus digit and dosing-token gates**, chosen from the dev distribution (docs/NORMALISATION.md). Document text stays optional; the live app cannot use it.
- **incomplete_quote** derives only from the model's output. One revision after dev results: the timing and frequency parts count only when the unsupported value survives or is a meal relation.
- **Safe-by-default flag tiers**: any flag not listed in NOTE_FLAGS is must_confirm. role_corrected was promoted to must_confirm (name-related, sat on a real error). conflict_* stay note (as must_confirm: 65% load, no extra error caught).
- **interaction_ready needs an EXACT printed name**; fuzzy-accepted names show resolved_generic but are never interaction_ready. schedule_ready excludes PRN and non-daily.

## Phase 3
- **Templates for medicines, model only for free text**: medicine lines are deterministic and reviewable; the model never writes a dose, name or schedule.
- **Fallback rule**: a language text that fails verification is replaced by the original extracted English plus a notice, per language. Unverified text is never labelled verified; the rejected text is kept in the verification record for reviewers only.
- **Verified = all deterministic checks AND judge supported**. Thresholds (verification.py, script.py): English >= 0.9 Latin letters; Tamil/Hindi >= 0.8 target-script letters outside Latin tokens (fails closed when none); length bounds; numbers compared as sets with Unicode digits normalised; drug names compared against the formulary in both directions.
- **Batch anomalies fail the batch**: an extra id or changed order fails every line of that batch; a missing or duplicate id fails that line.
- **Tamil chunking** (4 lines, per-line retry) and failure caching: a code fix for repetition loops, not a prompt change. Hindi stays one call per document.
- **Prompt v2 kept** (one of two revisions used): only the translate prompt changed (general rules). Numbers in docs/EXPLANATION_PROMPT_LOG.md.
- **Probe lines** for the drug-name and urgency corruption types because dev lines contain neither; labelled as probes, not from dev documents.
- **No new dependencies**: readability, script detection and CSV use the standard library.

## Phase 3e
- **Phrase library before the model, exact match only**: reviewable text for common lines, no model call, no fuzzy matching; near-misses are reported, never shown. A different number, negation, symptom or extra clause falls through to the model path.
- **Provenance and labels**: `model_checked` can never be labelled as human-reviewed; authored English carries no label. Per-language provenance is authoritative (languages fall back independently).
- **Blind authoring** of library and stress set so dev coverage and stress results are not tuned; the library is not extended from dev near-misses.
- **Dev re-run re-batches** the model items (matched lines removed), so documents with a match lose their cached batch; Tamil moved -2 points from batching noise.
- **No prompt revision** (see EXPLANATION_PROMPT_LOG.md). The `you have` regex finding is left for the user to decide (code rule, outside this phase).
- **Placeholders `{n}` only, integers 1-3 digits without leading zero, per-phrase range**; phrase corrections may not add or drop a number.

## Phase 4
- **Coverage rule rejected (2026-10-16)**: the ATC-letter coverage rule had 96 violations (pairs in the downloads that the rule called not covered). Authored letters cannot be validated (every drug appears as a partner in all 8 files; secondary and combination ATC codes). Absence from a partial download is uninformative, so the product has only four statuses: `interaction_found`, `not_checked_no_record`, `not_checked_unconfirmed`, `not_checked_database_missing`. No "no interaction listed" and no "not covered" status exists. Evidence archived in `scripts/evidence/`; the formulary ATC pharmacist sheet is dropped; the formulary review sheet covers brands, strengths, forms and routes only.
- **Phase 4-0**: the `you have` diagnosis rule ignores conditional clauses (if, when, whenever, unless, in case; up to three words between); see EXPLANATION_PROMPT_LOG.md.
- **Strict plus flag-covered silent-miss metric (Phase 4-5)**: strict per-pair matching reports 3 misses caused by the evaluator failing to match a garbled row; the pass/fail metric counts a ground-truth interaction as covered only if both medicines have an extracted row (matched or assigned one-to-one from unmatched not-ready rows) with engine status found/unconfirmed. The document-level banner is not a criterion.
- **Guardrail blames a model line only for families absent from its source**, so faithfully copying the doctor's own instruction is not rejected; fixed templates are scanned without a source.
- **Supplement `basis`**: pair_specific_label (5) or class_statement_applied (11); the pharmacist confirms class membership.
- **Attribution line is English only** and lives in templates.json under `english_only` (not in review sheets).

## Phase 5
- **No accounts**: anonymous browser session, random token in an HttpOnly SameSite=Lax cookie; only its SHA-256 is stored; 24 h lifetime, lazy plus periodic erasure.
- **SQLite** (stdlib, versioned migrations), journal_mode=DELETE and secure_delete so deleted rows leave no WAL; all content payloads Fernet-encrypted with the id and kind inside the envelope. Key from `scripts/generate_data_key.py`, never printed.
- **Photo discarded by default**; opt-in `keep_photo_for_session` stores it encrypted (needed for retry only).
- **Data origin**: `user_upload` is processed only by the localhost Ollama adapter (Gemini fails closed) and never touches `data/cache` (`extract_bytes`, `narrative.NO_CACHE`). Synthetic behaviour is byte-identical.
- **Confirmation overlay** is a pure function over the normalised extraction; the frozen safety engine runs on the overlay. Name reasons clear only by choosing a formulary drug or confirming an exact identity (stricter than the brief: also missing_name, multiple_drugs_in_quote, possible_combination). Non-daily is never schedule_ready.
- **Raw-body upload** (not multipart) to avoid a new dependency; OpenAPI declares image/png and image/jpeg.
- **One worker, bounded queue**; narrative per language starts in the background at awaiting_confirmation, so confirmation overlaps it. Free-text lines show "still preparing" until ready.
- **Reworded** the limit-reached string so the frozen "you have" guardrail rule does not flag it; the rule itself was not changed.

## Phase 5c: prototype review mode
- **Prototype decision (project owner)**: this is a working prototype without clinical validation and no independent reviews will arrive in time. The review step is replaced by an honest author self-check with explicit labels. Nothing may be labelled reviewed by a pharmacist or native speaker unless that happened; no person's initials go in a reviewer field; Tamil/Hindi stay `draft_unreviewed` and no new translation status was invented.
- **`author_checked` status** (supplement only): enabled by the loader like `reviewed`, but carries `checked_by` (fixed `author_prototype_selfcheck`), `checked_on`, `basis` and `evidence {url, section, note}`; an entry missing any of them is ignored (fail closed). Source label `curated_author_checked`; user text says the interaction "may" occur, names the source type and "not checked by a pharmacist". Separate import mode `--author-selfcheck` can only produce `author_checked` and the normal mode can only produce `reviewed` (tests). Self-check fields are named `selfcheck_*`, never `reviewer_*`.
- **Why**: gives the supplement real, auditable evidence without pretending to a pharmacist review, and keeps the upgrade path (normal import) intact.
- **Self-check result**: all 16 pairs agree against official sources; class membership was supported by official pages (labels, WHO ATC for gliclazide). Corrections: S01 basis is pair-specific; S05 source changed (the recorded Micardis URL now returns the Micardis HCT label); S06, S07 and S09 summaries rewritten where the old summary said more than the source. Severity unchanged (only S11 is `major`, because the source states contraindicated).
- **Guardrail left unchanged**: no logic edits; the new strings pass it without allow-list entries (`safety.author.major` was tested without one). Only report plumbing changed in the engine (`supplement_author_checked` field) so the right attribution line is chosen; decision logic is untouched.
- **Attribution/notice templates**: one new attribution variant (used when any author_checked entry exists) and a brand-mapping notice shown whenever the interaction section is displayed, with ta/hi drafts.
- **Contact setting**: `CONTACT_NAME` (default Demian) and `CONTACT_EMAIL` (default empty, never in the repository); the consent contact line shows the name alone when the email is empty. Notice version 2 (hash pinned); consent under v1 is asked again.

- **S11 source note (domperidone + levofloxacin)**: the current UK SmPC on emc.medicines.org.uk was read as corroboration only. The evidence of record is HPRA and EMA. This is an exception to the regulator-domains-only network rule, accepted by the project owner (Phase 6a-0).

## Phase 6a: frontend design system, shell, ambient layer, landing
- **Wording of "not checked never means safe"**: the owner's copy rules ban the word "safe" and also ask for this statement. The how-it-works note says "Could not check only means we found no information... It is not a sign that the medicines go well together." A test bans the forbidden words in all `ui.*` English copy.
- **Strings**: every visible string is a `ui.*` template exported to `strings.generated.json` (a test fails when stale), so the landing works with the backend off; the landing's sample line is copied from the existing `schedule.notice` template (no new translation). Footer does not show a contact: contact comes from the backend setting, so the footer points to the privacy page, which shows the notice's contact line.
- **Fonts**: only the needed subset/weight CSS files are imported (Latin, Tamil, Devanagari; 400/600; variable Fraunces). Letter-spacing and uppercase labels are switched off for ta/hi because tracking breaks Indic conjuncts; display sizes are smaller for ta/hi.
- **Ambient layer**: Canvas 2D + CSS only. Particle field is a fixed canvas at z-index -1 inside the content stacking context so it never covers text; frame stats are collected only in development or with `?perf=1`. Duotone photographs use CSS blend modes (pine background, grayscale image with `screen`, paper layer with `multiply`), no SVG filters.
- **Photos**: Wikimedia Commons only, CC0 or CC BY (no share-alike because the site adapts the images); search stopped at HTTP 429. Source data lives in `assets/photo_sources.json`; `prepare_photos.py` generates the manifest, responsive files and `ATTRIBUTION.md`. A photo with readable text was cropped to its text-free half. CC BY credits are shown in the footer.
- **Tests compile outside `tsc -b`** (`*.test.ts` excluded from tsconfig.app) so the app build needs no Node types.
- **Backend-off tests** use Playwright request blocking (same effect as a stopped server for the browser).

## Phase 6b-0: negated "safe" is the one allowed use
The how-it-works note now reads "This does not mean they are safe." (en; ta/hi drafts) instead of "not a sign that the medicines go well together". The 6a forbidden-word test strips exactly that sentence and nothing else; the English guardrail scan passes it by negation, so no ALLOW entry was added and guardrail logic is unchanged. A test now scans all English ui.* strings with the guardrail.

## Phase 6b decisions
- **Data router**: `createBrowserRouter` so `useBlocker` can guard unsaved decisions (the leave dialog); `FlowProvider` lives inside the Shell route.
- **State is memory only**: the flow reducer is rebuilt from the API after a reload; nothing but language and calm mode is stored (source scan test + Playwright audit). The photo is an in-memory Blob URL; after a reload it is fetched from the server only if the person chose to keep it.
- **Review semantics**: one explicit "Use this check" per card; the save posts the FULL set of decided cards (the endpoint replaces); undecided medicines are left out and stay unconfirmed; nothing is preselected or guessed; name reasons are cleared only through the picker.
- **Request contract, not response contract**: openapi.json has no response schemas, so types for requests are generated and checked, responses are hand-typed. Proposed for later (backend, not done here): add response models.
- **Server text first**: errors, confirmation strings, schedule and results come from `GET /strings` and `/result`; `ui.flow.*` text is used only for client-side states or as fallback.
- **Timers**: only polling (stops on terminal states, pauses when hidden) and a 60 s refresh of the "next dose" label; no alarms, no notification permission.
- **Shell fix**: `useOutlet()` inside AnimatePresence instead of `<Outlet/>` (double mount bug found by the live run).
- **Live test hygiene**: never rebuild the preview while a run is in flight; the default Playwright config ignores `e2e/live/`.

## Phase 6c decisions
- Review list order follows the API `review_level` only, never the local checked state, so a card does not jump while the person works; checked cards fold, must-confirm cards are always open (fail closed).
- Tamil header switches to the menu below 80rem and Tamil always uses the vertical how-it-works flow: Tamil labels are about twice as wide and cut off in a fixed row/SVG.
- Public routes make no session call: `FlowProvider` boots only on flow paths, so no 401 in the console.
- Alt text of `ui.photo.pillbox` and `ui.photo.water` corrected after looking at the images (an inaccurate alt is a defect); ta/hi redrafted as draft_unreviewed. Existing ids kept so no code changes.
- No new dependencies; images via Pillow; ambient layer unchanged (Canvas 2D, CSS transforms).

## Phase 6d decisions
- **Flaky phones test**: root cause was the web font still loading (fallback font wider, text overflowed the notice by a few px at 320 px in Tamil) when the test measured; the test now waits for `document.fonts.ready` and `.notice-body` wraps with `overflow-wrap: anywhere`. A timeout was not raised.
- **Demo data is recorded from the real API, not hand-written**: `scripts/build_demo_data.py` runs the real FastAPI app in-process (throw-away database and key) with the extraction replayed from the cached model output of dev document ds_037 (condition `poor`) and the narrative from the on-disk cache with a provider that raises on a miss. Every fixture is therefore shaped exactly like a real response and nothing in it was typed by hand. Document choice: it has 4 medicines, a garbled name ("Netfornin", read from the poor photo) that exercises the picker, a second must-confirm row (duplicate name fields), 5 interaction pairs after confirmation and cached narrative in en, ta and hi.
- **DDInter exception (deliberate)**: the fixtures contain 5 DDInter-derived pairs (names and level only) with the attribution line; raw files and the derived store stay untracked. See docs/DDINTER_COVERAGE.md (addendum); a test enforces the limit.
- **Demo mode = a second transport, not a second app**: under `/demo` the same typed client functions are answered from the bundled fixtures in memory (no `fetch`, no session, no storage); the real pages are reused. After Save the pre-recorded AFTER result is returned whatever the person chose, and the page says so.
- **Delete control in the collapsed header (6d)**: moving the one-row header breakpoint out (70rem, Tamil 96rem) for the new Testing link hid "Delete my data" behind the menu for Tamil desktops at 1280 px; a live flow stalled on it (a test could not find a visible control; the backend was fine, see PRIVACY.md section 9). Decision: from 768 px, while the header is collapsed, a 44 px trash icon button (accessible name and tooltip from the existing `ui.flow.delete.button`, tooltip on hover and focus) sits beside Menu; the full-text button stays in the menu, the footer and /documents. Below 768 px it stays in the menu (the Menu button must stay on screen at 320 to 390 px). Reachable in at most two interactions at every width (tested 320 to 1920 px, en/ta/hi).
- **Tests that press delete share one helper** (`pressDelete`, `openMenuIfCollapsed` in e2e/flowhelpers.ts) so the pattern cannot recur. Live specs use 45 s for ordinary UI steps; only waits for backend work (extraction, narrative) keep long, commented timeouts, so a missing control fails within about a minute.

## Phase 7a decisions
- **Pre-registered one-shot test**: protocol written and committed before the harness (docs/FINAL_TEST_PROTOCOL.md). The runner refuses without `--final-test-run`, with a dirty tree (except `eval/test_runs.log`), on freeze-manifest drift, without the tag `freeze-pre-test` on HEAD or an ancestor, with a model digest or test-data hash that differs from the pins, and a second official run (`--rerun-reason` writes a labelled `final-test-v1-posthoc-N`). Results get a SHA-256 checksum file that marks completeness.
- **Pins are created in 7b, not 7a**: the model digest (asked from the local Ollama API) and the set hash of the test documents are written by `--pin` at the start of 7b. Hashing the test files in 7a would have broken the test-split lock. The pin files are deliberately not frozen files.
- **Own bootstrap and Wilson code** (standard library, seeded 20261018, 2000 resamples, tested against known values) instead of a statistics dependency; the bootstrap unit is the document (pooled: the document with all conditions).
- **Pair-level DDInter levels are never committed** in final results (`scrub_safety`): aggregated counts only. The stress set commits drug lists and categories, not levels or expected statuses.
- **Stress set** (30 prescriptions, 10 categories x 3, own seed): the eye-drop category uses timolol, which is not in the formulary (the formulary has no eye drop); every other medicine is a formulary drug. `eval/stress/run_safety_stress.py` is new because `eval/stress/run_stress.py` is the older verification-stack stress test. `eval/phase4_safety.evaluate` got an optional `split` argument (default dev) so the final run can reuse it.
- **Real-photo scorer drives the real API** (session, consent, upload, medicines endpoint) and scores final values after normalisation with the existing scorer; it refuses unmapped files and prints ids and counts only.
- **Usability pack**: five participants are a formative check, not a statistic; the quiz has two critical wrong answers (believing "could not check" means safe; acting on the interaction list alone).

## Phase 7b write-up decisions
- **Results folder read-only; audit copy.** `eval/results/final-test-v1/` is never edited. The gitignored `eval/test_runs.log` is copied (force-added) to `eval/results/final-test-v1-audit/` with its own SHA256SUMS, so the history (one pin, ONE official run, one refused second attempt) is part of the record.
- **Independent recomputation is limited to what the CSV holds.** `per_document.csv` has only medicine counters, so `scripts/verify_final_results.py` recomputes precision, recall, F1, fully-correct, hallucinated, invented rate and all their intervals, and checks the flag, safety and operational numbers for internal consistency (pooled = sum of conditions, shares = n/N, attempted = scored + skipped). Identical, except 3 bootstrap bounds that differ by 0.0001 because `eval/matching.py` computes F1 from precision and recall already rounded to 4 decimals. Name errors, silent misses and explanation figures cannot be recomputed from the CSV.
- **Freeze-manifest drift is expected.** `scripts/freeze_manifest.py verify` now reports drift for `data/templates/templates.json` (the Testing page needed new `ui.*` strings). The manifest is a pre-run artefact and is NOT re-written; the tag `freeze-pre-test` is NOT moved. The official run used the frozen state; the other files the page needed (builder, page, css, p6d strings, tests) are not in the manifest.
- **Test rows are pooled and complete, not selected.** The Testing page lists every primary protocol metric pooled over the five conditions (66 rows); per-condition detail is under "also measured". Unfavourable rows (2 wrong schedules, 1 unflagged wrong name, Tamil verification 0.180) are shown like the rest.
- **Dev beside test, flagged honestly.** The dev value comes from the results file's own `dev_vs_test` table (no second source); the page states when it lies outside the test interval (descriptive, not a hypothesis test; Wilson intervals ignore clustering within documents).
- **The builder verifies the official folder.** It checks SHA256SUMS first (either line ending, because per_document.csv is written with CRLF) and fails if the official results changed.
- **No change to the system in response to the results.** The post-hoc error analysis is descriptive; any fix needs a new freeze and a labelled post-hoc run.
- **7b-posthoc is read-only and descriptive.** The case review opened test ground truth and cached outputs at the user's explicit request; nothing was changed in response, no re-run, no new official number. Outputs live only in `docs/FINAL_TEST_POSTHOC.md` and `eval/results/final-test-v1-posthoc/`; `docs/FINAL_TEST_RESULTS.md` gained only a pointer section. Excerpts stay at field level.
- **Standardisation by difficulty only.** Templates have 1 to 8 documents per split, so only the three difficulty strata are reweighted (weights = share of each metric's denominator); both directions are reported because they can disagree.
- **Cluster bootstrap for medicine-level proportions; not for rare events.** Seed 20261028, 2000 resamples over the 40 documents. For the 2 wrong schedules the percentile bootstrap is narrower than Wilson and is explicitly not used as evidence; the Wilson bound and the document count are quoted instead.

## Phase 7c-lite decisions
- **Ollama version deviation accepted.** The stress run used 0.40.11 against the pinned 0.40.5 (same model digest) by the owner's decision; the pin file is not changed, the deviation is in the protocol, run manifest, STRESS_RESULTS and LIMITATIONS, and stress numbers are not compared with `final-test-v1`.
- **New runner instead of changing the harness.** `eval/stress/run_safety_stress.py --mode extraction` was a minimal stub (no per-document table, overlay, intervals or manifest). Instead of editing it, `eval/stress/run_stress_extraction.py` was added (resumable from gitignored `eval/runs/<run-id>/raw`, `extract_bytes` so no shared cache; matching on the normalised names the engine sees). It measures what the protocol pre-registered; no system code was touched.
- **Counts per pair, not pair lists.** Per-document table carries counts and statuses only; levels appear only as aggregated counts (DDInter-derived data is not committed pair by pair).
- **Scripted overlay**: ground-truth names pick the formulary drug for flagged names, all non-name reasons are acknowledged, hallucinated medicines would be removed; testing only.
- **Hallucinated interaction_ready medicines** have no ground-truth identity: reported separately (0 occurred), not in P3.
- **Page**: one stress section (`stress_ext`), pooled per render with Wilson and, where the file has one, bootstrap intervals; per-category tables and flag causes stay in STRESS_RESULTS (cause counts are not shares, so no interval). Rows use `data-sfigure` so the older testing specs are unchanged.
- **Freeze drift** (recorded, manifest and tag not touched): `data/templates/templates.json` (85 new `ui.testing.s.*` and `ui.testing.split.stress` ids) and the added file `eval/stress/run_stress_extraction.py`. Files changed for the page: `scripts/build_testing_page_data.py`, `frontend/src/pages/TestingPage.tsx`, `frontend/src/styles/flow.css` (two small classes), generated JSON files.
- **Version sanity check** ran with `extract_document(use_cache=False)` into a gitignored scratch folder; the shared cache was only read.

## Phase 8a decisions
- **Public-history scan before anything else.** `scripts/scan_repo_history.py` (read-only, stdlib; redacts every match; tested on a synthetic repo) found no secret and no private file in any of the 110 public commits. Ten `.log` paths matched the "never tracked" list (one intentional audit copy; nine history-only start-up and request logs, three with one Windows user-path mention); the owner accepted them (option A): no history rewrite, no force-push, tag `freeze-pre-test` untouched. Summary: `docs/REPO_SCAN.md`.
- **Licence: MIT (owner decision), superseding the earlier "no LICENSE until decided" instruction.** `LICENSE` (Copyright (c) 2026 Demian, no e-mail) covers the project's own code, documentation and the synthetic documents and datasets it authored. It does NOT cover third-party material: the small DDInter-derived excerpt in the sample fixtures (CC BY-NC-SA 4.0), the photographs (`assets/ATTRIBUTION.md`), the fonts (OFL-1.1) and library code (GSAP has its own "no charge" licence). Reason: the repository is already public, the owner wants others able to read and reuse the code, and the exclusions keep the non-commercial, share-alike data outside MIT. A note sits in `frontend/src/demo/fixtures/README.md`; `backend/tests/test_license_files.py` fails if LICENSE or the note is missing. No "licence not yet chosen" statement existed in any tracked file (searched); `package.json` licence fields and lockfiles were not changed.
- **README repaired and split.** Control characters in README.md (8 lines) and docs/PROGRESS.md (2 lines), from Windows backslash sequences, were repaired (`backslash-b`, `-a`, `-f`); `backend/tests/test_no_control_characters.py` guards all tracked text files. The long per-phase command lists moved unchanged to `docs/COMMANDS.md`; README is now a public overview.
- **.gitignore** gained `*.db`, `*.sqlite`, `*.sqlite3`, `*.key`, `*.pem` (nothing tracked matched; nothing was untracked).

