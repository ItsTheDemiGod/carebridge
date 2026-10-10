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
