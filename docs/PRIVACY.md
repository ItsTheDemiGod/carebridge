# Privacy and security design (Phase 5)

> **Not legal advice. Not reviewed by a lawyer.** The DPDP checklist below is an engineering self-check for a college prototype, not a compliance claim. This is a class project prototype and not medical advice.

CareBridge is a local-first prototype. A user photographs a medical document; a local model (Ollama on the same computer) reads it. Nothing is sent to an external service. There are no user accounts: an anonymous browser session owns the data. This document was written before the code and is updated at the end of the phase (section 7).

## 1. Data inventory

| What | Where | Why | How long | Encrypted | How it is deleted |
|---|---|---|---|---|---|
| Session token (random, 256 bit) | Browser cookie (HttpOnly, SameSite=Lax) | identify the anonymous session | until session ends or TTL (24 h) | n/a (secret) | cookie cleared by `DELETE /session`; expires |
| SHA-256 hash of the token | `sessions.token_hash` | look up the session without storing the secret | until deletion/expiry | hashed (one way) | row deleted |
| Language, created/last_seen/expires | `sessions` | show the right language, enforce expiry | until deletion/expiry | no (no health content) | row deleted |
| Consent record (notice version, notice sha256, language, purposes, time) | `consents` | evidence of itemised consent | until deletion/expiry | no (no health content) | row deleted with the session |
| Document row (random id, state, error code, progress/timings, image_kept) | `documents` | job state | until deletion/expiry | no (no content, only states and timings) | rows deleted |
| Extracted + normalised medicines, follow-ups, warnings, advice | `payloads` kind `normalised` | the results the user asked to store | until deletion/expiry | **yes** (Fernet) | rows deleted, then VACUUM |
| Model-written narrative (simplified/translated lines, judge output) | `payloads` kind `narrative` | explanation text | same | **yes** | same |
| User confirmations (including the optional 80-character note), audit trail | `payloads` kinds `confirmations`, `decisions` | confirm-first flow | same | **yes** | same |
| Schedule edits | `payloads` kind `schedule_overrides` | user-edited times | same | **yes** | same |
| Photo (processed, metadata stripped) | `payloads` kind `images` only if `keep_photo_for_session` consented | allow retry / viewing | same | **yes** | same |
| Photo when not kept | RAM of the API process only, dropped after the extraction step | extraction | seconds to minutes | n/a | garbage collected (see limits) |
| Adherence events (med_ref index, scheduled time, date, taken/skipped) | `adherence_events` | tracking | same | **no** (structured, no names, no free text) | rows deleted |
| Logs | stderr | operations | process lifetime | no | contain only random ids, states, timings, status codes, error codes |
| Shared caches (`data/cache`) | disk | speed up *synthetic* evaluation | n/a | n/a | **never written for a user upload** (tested) |

Not stored anywhere: names, accounts, email, IP address, the original unprocessed upload, EXIF/GPS data, free-text medicine names.

## 2. Data flow

1. **Consent.** The notice (en/ta/hi) is shown; the user grants itemised purposes (`process_photo` and `store_results_for_session` are required; `keep_photo_for_session` is optional, default off). Without a consent for the *current* notice version every data endpoint returns 403 `consent_required`.
2. **Upload.** Raw image bytes in the request body. The server checks size, magic bytes, Pillow decode, pixel limit, takes the first frame, applies EXIF orientation, re-encodes (all metadata dropped). The processed bytes stay in memory; they are written encrypted only if the optional purpose was granted.
3. **Extraction.** A single worker thread sends the image to the local Ollama model (localhost only, data origin `user_upload`; Gemini is refused for this origin). No disk cache. Text inside the image is data, never instructions.
4. **Normalisation.** Rule-based, in memory; the result is encrypted and stored. The image bytes are dropped (unless kept).
5. **Narrative.** The free-text lines (advice, follow-ups, warnings) go to the local text model in the background while the user confirms medicines. Output stored encrypted. No disk cache.
6. **Confirmation.** The user's decisions replace the previous set (encrypted). The overlay (a copy of the normalised document) feeds the unchanged safety engine.
7. **Result / schedule / summary.** Assembled on demand from the encrypted payloads; returned as JSON with `Cache-Control: no-store`.
8. **Adherence.** Taken/skipped events keyed by medicine index, no free text.
9. **Deletion.** `DELETE /session` removes the session and everything linked in one transaction, then runs VACUUM (with `secure_delete`), clears the cookie, returns a counts receipt (not stored). Expired sessions are swept at start-up and every few minutes.

## 3. Threat model

| Threat | Mitigation | Covered by test |
|---|---|---|
| Another session reads my data (IDOR) | random 128-bit document ids; every query filters by the session of the cookie; foreign ids give 404 (not 403) | generic IDOR test over all routes |
| Stolen database file | all content payloads and images are Fernet-encrypted; the document id and kind are inside the authenticated envelope, so blobs cannot be moved between rows; the tokens are stored hashed | encryption tests, canary test |
| Content leaking into logs | central logging policy: ids, states, timings, status codes, error codes only; no request bodies, no exception text from user content | logging test, canary test |
| Content leaking into caches or temp files | user_upload origin never writes `data/cache` (extraction and narrative); no temp files are created; SQLite journal mode DELETE (no WAL) | cache-untouched test, canary test over `data/` and temp |
| Oversized upload / decompression bomb | `Content-Length` and streamed byte cap; pixel limit checked before decode (`Image.MAX_IMAGE_PIXELS`); first frame only | upload tests |
| Wrong file type / disguised file | magic bytes must match the declared type, then a real decode; PDFs and everything else rejected | upload tests |
| EXIF location data | image re-encoded after orientation fix, so all metadata is dropped | EXIF test |
| Prompt injection inside the image | model output is validated against the schema; text from the image is shown only as data; the model has no tools; medicines need the user's confirmation before they are checked or scheduled; guardrail scans English output | normalisation/guardrail tests (earlier phases), confirmation tests |
| Cross-site requests against the local API | CORS limited to `ALLOWED_ORIGINS` with credentials; every state-changing request needs the custom header `X-CareBridge-Request: 1` (forces a CORS pre-flight) and an allowed `Origin`; SameSite=Lax cookie | CSRF tests |
| Session token theft | HttpOnly cookie (no script access), `Secure` when behind HTTPS, token only in the cookie (never URL/body), 24 h absolute lifetime, hash stored; `DELETE /session` kills it | cookie tests |
| Uploaded data sent to a third party | Gemini adapter refuses `user_upload`; Ollama adapter accepts only localhost | provider tests |
| Error messages leaking content | one error format, no echo of user content, no stack traces | error-format tests |

## 4. DPDP Act 2023 checklist (engineering self-check; NOT legal advice; NOT lawyer-reviewed)

| Duty (plain language) | What the prototype does | Gap |
|---|---|---|
| Plain-language notice | consent notice in English, Tamil, Hindi, short sentences | Tamil/Hindi are drafts until native review; the contact line comes from settings CONTACT_NAME (default Demian) and optional CONTACT_EMAIL; notice v2 says it is a prototype, ta/hi are machine-drafted and the interaction data is author-drafted and not pharmacist-reviewed; consent given under v1 is asked again |
| Itemised consent | three separate purposes, two required, one optional and off by default; version + hash of the notice stored | no consent manager integration |
| Purpose limitation | data used only to extract, explain, check and schedule for this session | none known |
| Data minimisation | no accounts, no names, photo dropped by default, metadata stripped | the extracted text still contains health data by nature |
| Retention limit | 24 h absolute session lifetime, then complete deletion | cannot control backups of the machine |
| Erasure on request | one button/call erases everything and returns a receipt | residue limits in section 5 |
| Security safeguards | encryption at rest, access control per session, input validation, no external transfer | key stored on the same machine (section 5) |
| Children / verifiable parental consent, data-breach notification, grievance officer | **not implemented** | out of scope for a class prototype; the contact person is a name from settings, with no grievance process |

## 5. Honest limits

- **Deletion is logical + VACUUM.** SSD wear levelling, the file system journal and OS caches can keep old pages. `secure_delete` and VACUUM overwrite within SQLite but not the physical medium.
- **Process memory.** Decrypted data, the processed photo and model output live in Python memory while used; they are not zeroed.
- **OS swap / hibernation** may write memory to disk.
- **Backups and file-history** of the laptop are outside the app's control.
- **Browser history/cache.** API responses are `no-store`, but the browser, extensions and screenshots are outside our control.
- **The data key lives in `backend/.env` on the same machine as the database.** Encryption protects a copied database file, not someone with access to the whole machine/account.
- **Ollama** runs as a separate process with its own memory and may keep prompts in its context cache while the model is loaded.
- Adherence events are stored unencrypted (structured, no names) so they can be summarised cheaply; they still reveal that medicines were taken at certain times.
- An anonymous session has no recovery: clearing cookies loses access until the 24 h expiry sweep removes the data.
- A wrong user selection from the formulary picker gives results for the wrong drug (see `CONFIRMATION.md`).
- Nothing here is certified; no penetration test was done.

## 6. Key handling

`CAREBRIDGE_DATA_KEY` (a Fernet key) is created by `scripts/generate_data_key.py`, which appends it to `backend/.env` only if absent and never prints it. The application refuses to start without it. Losing the key makes stored payloads unreadable (acceptable: data is short-lived). Never commit `.env`.

## 7. End-of-phase status

Offline tests: 716 pass (canary, cache-untouched, logging, Gemini fail-closed, IDOR over every route, CSRF, upload hardening, encryption, deletion, expiry).
Live smoke (`docs/smoke/phase5_live_smoke.json`, clean and poor ds_037, real local model): full flow ran, deletion left 0 rows for the session (checked through a read-only SQLite connection), the server log held 0 occurrences of medicine or advice words.
Not done / needs a human: lawyer review of the DPDP checklist and consent notice; native review of Tamil/Hindi consent, deletion and error strings (`data/templates/review_sheet_phase5_new.csv`); hosting is out of scope (cookie `Secure` and HTTPS must be set when deployed).

## 8. Browser side (Phase 6b)

What the frontend keeps, and what it does not:
- **localStorage**: only `carebridge.language` and `carebridge.calm` (a language code and a 0/1 flag). Nothing else, ever (`src/privacy.test.ts` scans the source; the Playwright audit checks the running app after a full flow).
- **Not used at all**: sessionStorage, IndexedDB, Cache Storage, `document.cookie`, `history.pushState/replaceState` state, service workers. The only cookie is the backend's HttpOnly `cb_session`, which JavaScript cannot read.
- **Document ids** appear only in the route path (`/d/<id>/review`). They are never put in a query string, the page title, a hash or any external link; `<meta name="referrer" content="no-referrer">` is set. Page titles are `ui.title.*` strings (language only).
- **The chosen photo** lives only as an in-memory `Blob` and an object URL for the side-by-side view. It is uploaded once (raw body), never stored in the browser, and the URL is revoked when the person leaves the flow, replaces the photo or deletes their data. After a reload the preview is gone: the page says so and, if the person chose to keep the photo, fetches it from the server (`GET /documents/{id}/image`).
- **Results, medicines, decisions, schedule and adherence** are held in React state only and rebuilt from the API after a reload. Unsaved decisions are lost on reload (the page asks before leaving).
- **Rendering**: every server string is rendered as a text node. `dangerouslySetInnerHTML`, `innerHTML` and `insertAdjacentHTML` are banned (tested). The client never logs request or response bodies.
- **Network**: only the app origin is contacted (fonts, photos and scripts are self-hosted; no CDN or analytics). The Playwright audit asserts a single host.
- **Delete my data** (header, once a session exists) calls `DELETE /session`, then clears all in-memory state, revokes the photo URL and returns to the landing page with the backend's receipt text. A 401 (expired or already deleted) is treated as "nothing left".
Residual risks: browser extensions and the operating system can read page memory; a printed or saved PDF of the results leaves the app's control; the in-memory photo is visible to anyone using the same browser tab.
