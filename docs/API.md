# CareBridge API (Phase 5)

Base path `/api/v1`. JSON in and out (except the upload body and the kept photo). Machine-readable contract: [`openapi.json`](openapi.json) (`python scripts/export_openapi.py`; a test fails if the committed file is out of date). Privacy and threat model: [`PRIVACY.md`](PRIVACY.md). Confirmation rules: [`CONFIRMATION.md`](CONFIRMATION.md).

CareBridge explains and organises. It never diagnoses, never recommends a dose change, and says "an interaction was found" or "we could not check", never "safe".

## Security model
- **No accounts.** `POST /sessions` creates an anonymous session and sets the cookie `cb_session` (random 256-bit token, `HttpOnly`, `SameSite=Lax`, `Path=/api`, `Max-Age` = `SESSION_TTL_HOURS`, `Secure` when `COOKIE_SECURE=true`, which **must** be set behind HTTPS). Only a SHA-256 hash is stored. A valid cookie is reused by `POST /sessions`.
- **Cross-site protection.** Every `POST`/`PUT`/`DELETE` must send `X-CareBridge-Request: 1`; if the request has an `Origin`, it must be in `ALLOWED_ORIGINS` (default `http://localhost:5173`, `http://127.0.0.1:5173`). CORS allows only those origins, with credentials, and only `Content-Type` and `X-CareBridge-Request` as request headers. Missing header or bad origin gives `403 request_blocked`.
- **Responses** carry `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'`.
- **Access control.** Session ids and document ids are random (128 bit). Every document query is scoped to the cookie's session: another session's id behaves exactly like a missing one (`404 not_found`).
- **Consent gate.** Every document, schedule, adherence and summary endpoint returns `403 consent_required` until a consent for the **current** notice version exists. Session-only endpoints: `GET /session`, `POST /consent`, formulary.
- **Errors** always `{"error": {"code": "...", "message": "..."}}`; the message is the English template `error.<code>` (other languages: `GET /strings?lang=ta&prefix=error.`). Messages never echo user content; no stack traces.
- The server never produces HTML; every string is JSON data.

## Endpoints
| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/consent-notice?lang=en\|ta\|hi` | nothing | notice text, `version`, `sha256`, itemised `purposes` |
| GET | `/strings?lang=&prefix=` | nothing | static template text for the UI (error., job., status., confirm., picker., schedule., summary., consent., delete., label., heading., timing., banner., notice.) |
| POST | `/sessions` `{language}` | nothing | start or resume the anonymous session; sets the cookie (201 new, 200 resumed) |
| GET | `/session` | session | language, expiry, consent state, document count, limits |
| POST | `/consent` `{notice_version, purposes[]}` | session | `process_photo` and `store_results_for_session` required; `keep_photo_for_session` optional (default off) |
| DELETE | `/session` | cookie | **delete-my-data and withdraw consent**: erases everything, returns a receipt; 204 if nothing to delete |
| POST | `/documents` (raw image body) | consent | upload (202); `Content-Type: image/png` or `image/jpeg` |
| GET | `/documents` | consent | list |
| GET | `/documents/{id}` | consent | job state, narrative state per language, timings |
| GET | `/documents/{id}/image` | consent | the kept photo (404 unless `keep_photo_for_session`) |
| POST | `/documents/{id}/retry` | consent | re-run a failed job (only when the photo was kept) |
| POST | `/documents/{id}/languages` `{language}` | consent | start the narrative for one more language |
| GET | `/documents/{id}/medicines` | consent | extracted medicines with source quotes, reasons, allowed actions |
| POST | `/documents/{id}/confirmations` | consent | the full set of user decisions (replaces the previous set) |
| GET | `/documents/{id}/result?lang=` | consent | assembled explanation, safety section, labels, narrative status |
| GET | `/documents/{id}/schedule` | consent | suggested daily slots for schedule-ready medicines + `not_scheduled` |
| PUT | `/documents/{id}/schedule-overrides` | consent | user-edited times (replaces the set) |
| POST | `/adherence` | consent | log taken/skipped for a slot |
| GET | `/adherence?document_id=&from=&to=` | consent | list events |
| DELETE | `/adherence/{event_id}` | consent | remove an event |
| GET | `/documents/{id}/doctor-summary?from=&to=` | consent | plain summary to show a doctor |
| GET | `/formulary/search?q=&limit=` | session | prefix/substring search, `limit` ≤ 20, no fuzzy matching |
| GET | `/formulary/{id}` | session | one formulary entry |
| GET | `/api/health` | nothing | liveness |

## Job states
`documents.state`: `queued → extracting → normalising → awaiting_confirmation`, or `failed` (with `error_code`). `expired` and `deleted` are reserved: an expired or deleted session removes its rows, so a client sees `401` / `404` instead.
`error_code`: `ollama_unavailable`, `image_unreadable`, `context_truncated`, `image_not_received`, `timeout`, `interrupted` (process restarted while in flight), `provider_not_allowed` (the configured provider is not the local one; fail closed, nothing sent). `error_message` is the template `job.failed.<code>` in the session language.
`narrative` (per language, in the document view): `pending → running → ready | failed`; `not_started` appears in `/result` for a language nobody asked for. The narrative of the free-text lines **starts as soon as extraction is done, while the user confirms the medicines**.
Timings (seconds) in `timings`: `queued_s`, `extracting_s`, `normalising_s`, `narrative_<lang>_s`.
Expected duration with a local 8B model on an 8 GB GPU: extraction 30–40 s per image; English plus one more language about 90–160 s. Poll `GET /documents/{id}` (a few seconds apart).

## Retry rule
The uploaded photo is processed and discarded by default, so a failed job **cannot** be retried: `POST /retry` answers `409 retry_unavailable` and the user must upload again. If `keep_photo_for_session` was consented, the photo is stored encrypted and `retry_possible` is true on a failed document.

## Limits
`MAX_UPLOAD_BYTES` 10 MB (`413 upload_too_large`), `MAX_IMAGE_PIXELS` 40 million (`422 image_invalid`, checked from the header before decoding), `MAX_DOCS_PER_SESSION` 10 (`429 too_many_documents`), `JOB_QUEUE_MAX` 3 queued/running extractions (`429 queue_full` + `Retry-After: 60`), PNG and JPEG only (`415 unsupported_file`; PDF: `415 pdf_not_supported`, "Please upload a photo or image (PNG or JPG). PDF is not supported yet."). Images are decoded (first frame only), rotated by EXIF, re-encoded without any metadata.

## Error codes
| HTTP | code | when |
|---|---|---|
| 400 | `consent_invalid` | missing required purpose, unknown purpose, or not the current notice version |
| 401 | `no_session`, `session_expired` | no/unknown cookie; expired session (its data is removed) |
| 403 | `consent_required`, `request_blocked` | no consent for the current notice; missing `X-CareBridge-Request` or bad `Origin` |
| 404 | `not_found` | unknown id **or another session's id** |
| 409 | `not_ready`, `retry_unavailable` | extraction not finished; retry without a kept photo |
| 413 | `upload_too_large` | body over the limit |
| 415 | `unsupported_file`, `pdf_not_supported` | wrong/undeclared type or magic bytes; PDF |
| 422 | `invalid_request`, `invalid_confirmation`, `image_invalid` | schema/validation failure; a decision that breaks a rule; undecodable or too many pixels |
| 429 | `queue_full`, `too_many_documents` | busy (see `Retry-After`); per-session limit |
| 500 | `internal_error` | unexpected failure (type only is logged) |

## Examples
Start, consent, upload:
```
POST /api/v1/sessions            {"language": "ta"}                      -> 201 {"language":"ta","expires_at":"...","consent":{"granted":false,"current_version":"1","purposes":[]},"documents":0,"limits":{...}}
POST /api/v1/consent             {"notice_version":"1","purposes":["process_photo","store_results_for_session"]}
POST /api/v1/documents           <PNG bytes>   Content-Type: image/png    -> 202 {"id":"Vm6V...","state":"queued","error_code":null,"narrative":{},"timings":{},"retry_possible":false,"confirmed":false,...}
GET  /api/v1/documents/Vm6V...   -> {"state":"awaiting_confirmation","narrative":{"en":"ready","ta":"running"},"timings":{"queued_s":0.0,"extracting_s":31.2,"normalising_s":0.0,"narrative_en_s":44.1},...}
```
Medicines review (excerpt):
```
GET /api/v1/documents/{id}/medicines
-> {"medicines":[{"index":0,"ref":"m0","as_written":{"brand":"Netfornin","generic":"Glibenclamide"},"printed":{...},"resolved_generic":null,"strength":"500 mg",
     "frequency":{"times_per_day":2,"timing_label":"after_meals","is_prn":false,"original_abbreviation":"BD PC"},"source_quote":"Tab Netfornin 500 mg ...","review_level":"must_confirm",
     "reasons":[{"id":"unresolved_name","template_id":"confirm.flag.unresolved_name","text":"...","kind":"name"}],"interaction_ready":false,"schedule_ready":false,
     "allowed_actions":["confirm_as_extracted","select_formulary_drug","not_in_list","remove"],"current_decision":null}], "added_medicines":[], "dose_options":[...], "formulary_status":"unverified_requires_pharmacist_review"}
```
Confirmations:
```
POST /api/v1/documents/{id}/confirmations
{"decisions":[{"index":0,"action":"select_formulary_drug","formulary_id":"metformin","strength_choice":"500 mg"},
              {"index":3,"action":"confirm_as_extracted","acknowledged_flags":["unusual_strength"]}],
 "added_medicines":[{"formulary_id":"omeprazole","strength_choice":"20 mg","dose":"1 capsule","schedule":{"times_per_day":1,"timing_label":"before_meals","duration_days":14}}]}
-> {"confirmed":true,"medicines":[{"ref":"m0","resolution":"selected","interaction_ready":true,"schedule_ready":true,"review_level":"none","unresolved":[],"not_checked_reason":null},...],"removed":[]}
```
Result (top level; `explanation` is the `ExplanationDocument` with only the requested language in each `text`):
```
GET /api/v1/documents/{id}/result?lang=en
-> {"document_id","language","confirmed","confirm_first","narrative_status":{"en":"ready","ta":"running","hi":"not_started"},
    "explanation":{"sections":[{"id":"medicines","heading":{"en":"..."},"lines":[{"line_id":"med-0","kind":"medicine","text":{"en":{"text":"...","provenance":"template","label_key":null,...}},
                   "source_text":"...","review_level":"none","settled":true,"notices":[],"narrative_pending":false}]}, {"id":"safety",...}, {"id":"warnings",...}],"safety":{"pair_results":[...],"overall_state":"..."}},
    "medicines_meta":[{"line_id":"med-0","ref":"m0","resolution":"selected","provenance":{...},"labels":[{"template_id":"confirm.you_selected","text":"You chose this medicine from the list."}],...}],
    "removed":[],"guardrail_events":[]}
```
A free-text line whose narrative is not ready has `narrative_pending: true` and the text "Still preparing this explanation..."; a failed narrative shows the original extracted English with the fallback notice. The number of warning lines always equals the number of extracted warnings.
Delete everything:
```
DELETE /api/v1/session -> 200 {"deleted":{"consents":1,"documents":1,"adherence_events":2,"payloads":4,"images":0,"sessions":1},"deleted_at":"...","message":"Your data has been deleted and your consent is withdrawn.","receipt":"Deleted: 1 documents, 4 saved results, 0 photos."}
```
The receipt is not stored.

## Schedule data
Slots come from documented default anchors (breakfast 08:00, lunch 13:00, dinner 20:00, bedtime 22:00, morning 08:00, afternoon 14:00, evening 18:00, night 21:00; before meals −30 min, after meals +30 min; 2/day = breakfast+dinner, 3/day = +lunch, 4/day = +bedtime; 5–6/day are not auto-scheduled; unspecified timing = evenly spaced 08:00–22:00 with the notice that no meal timing was found). These are scheduling conveniences, not clinical statements; `schedule.notice` ("Suggested times only; adjust them to match your doctor's instructions.") accompanies every schedule. Only `schedule_ready` medicines get slots; `not_scheduled[].reason` is one of `not_confirmed`, `non_daily`, `as_needed`, `too_many_doses`, `no_identity`. Duration is shown as "About N days in total." and never extended. Adherence events are structured only (`med_ref` like `m0`/`a0`, `HH:MM`, `YYYY-MM-DD`, `taken|skipped`); no free text. The doctor summary reports counts only (taken, skipped, missed), the unconfirmed items, and the interaction lines exactly as shown, plus a fixed disclaimer.
