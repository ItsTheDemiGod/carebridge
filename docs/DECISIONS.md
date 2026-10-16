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
