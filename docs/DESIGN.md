# CareBridge design system (Phase 6a)

Direction: **calm clinical editorial**. Warm paper-toned backgrounds, deep pine-teal ink, soft sage, one terracotta accent used sparingly. It should read as a hand-designed print product, not a SaaS template.

## Anti-patterns (forbidden)
Purple or blue-purple gradients; a centred hero with three identical rounded cards; emoji as icons; generic stock-SaaS layout; glassmorphism; lorem ipsum; fake logos ("trusted by"), testimonials or statistics; "AI sparkle" imagery; neon glows; identical card grids; every section centred. Wanted instead: asymmetric editorial layouts, large serif headlines, thin rules, small-caps labels, numbered sections, whitespace, paper grain, duotone photographs, a hand-built icon set, an original wordmark.

## Tokens (`frontend/src/styles/tokens.css`, the single source of truth)
- **Colour**: paper `#f5efe3`, paper-2 `#ebe3d3`, paper-3 `#ddd2bc`, ink `#10302b`, ink-soft `#3f5a55`, pine `#1e4d45`, pine-deep `#143730`, sage `#a9c0a6`, mist `#dce6da`, terracotta `#c4572f` (decoration, large display, icons only), terracotta-ink `#9c3d1a` (small accent text). Severity: major `#8c1d1d`, moderate `#6f4300`, minor `#0c5559`, unknown `#484f4e`, each with a tinted background. Severity and status are ALWAYS icon + text + colour, with a different icon shape per level (`StatusBadge`).
- **Type**: Fraunces (variable, display) + Noto Sans (body). Tamil: Noto Serif Tamil (headings) + Noto Sans Tamil. Hindi: Noto Serif Devanagari + Noto Sans Devanagari. Stacks switch from `html:lang(...)`. Fluid scale: display, h1 to h4, body 17 px, small 15 px, label 13 px (uppercase and tracked in English; no tracking or case change in Tamil and Hindi because letter-spacing breaks Indic conjuncts). Indic text gets taller line height.
- **Spacing**: `--s-1` to `--s-10` (0.25 rem to 9 rem), fluid `--gutter`, `--measure` 62 ch, container 80 rem.
- **Radii**: 6 px, 16 px, 30 px, pill. **Shadows**: `--shadow-soft`, `--shadow-lift`. **Motion**: 140 / 260 / 640 ms, `--ease-out`, `--ease-inout`. **z layers**: ambient 0, content 1, header 20, skip link 50, cursor 60. **Breakpoints**: 40, 48, 64, 80 rem.
- **Grain**: inline SVG noise (`--grain`, no image file), one fixed layer at 7 % opacity.

## Fonts
Self-hosted through `@fontsource` packages, `font-display: swap`. Only these files are imported: Fraunces variable (wght), Noto Sans latin 400/600, Noto Sans Tamil tamil 400/600, Noto Sans Devanagari devanagari 400/600, Noto Serif Tamil tamil 600, Noto Serif Devanagari devanagari 600. Each `@font-face` has a `unicode-range`, so the browser downloads only the scripts a page uses.

## Components (`frontend/src/components/`)
`Icon` (19 hand-drawn stroke icons on a 24 px grid, 1.5 px stroke, `currentColor`, `aria-hidden` unless a `label` is given), `Button` / `ButtonLink` (primary, secondary, quiet; focus ring; disabled and loading), `TextLink`, `Tag` (neutral, accent, draft), `StatusBadge`, `Notice` (info, caution, important), `Container`, `Rule`, `SectionHeading` (numbered small-caps label + serif heading), `Photo` (duotone with blend modes, lazy, explicit width and height, required alt, designed placeholder when the file is missing), `Tile` (mosaic tile: tone and pattern). Components contain no visible text of their own; labels come from props, which come from the generated strings.

## Contrast
`npm run check:contrast` computes WCAG ratios for every text and UI pair the tokens are used for (35 pairs; text 4.5:1, large text, icons, control boundaries and focus rings 3:1), prints a table and exits 1 on any failure.

## Motion rules and budget
Canvas 2D and CSS transforms only. No WebGL, no `backdrop-filter`, no blur on large areas. Particles: at most 60 on desktop, 24 on small screens, devicePixelRatio capped at 1.5, a capped number of faint connecting lines, loop paused when the tab is hidden, in calm mode, under reduced motion and on processing screens. Cursor ring only for `(pointer: fine)` without reduced motion; the native cursor stays visible; the ring never takes pointer events. Tile drift uses `translate` only. Reveals and the small parallax are off under reduced motion and calm mode. Page transitions are short. **Calm mode** (header toggle, stored in localStorage) turns off particles, cursor ring, tile drift and parallax.

## Accessibility (WCAG 2.2 AA baseline)
Skip link, landmarks, `lang` follows the selected language, visible focus (3 px ring, offset), full keyboard operation, 44 px minimum touch targets, text readable at 200 % zoom, contrast checked by script, severity never by colour alone, axe run on every route.

## Honest-copy rules
No claim of accuracy, speed or "AI-powered diagnosis". The words safe, safely, guaranteed, accurate, certified, clinically validated and doctor-approved are never used in the English copy (tested). Nothing implies a pharmacist, doctor or native speaker reviewed anything. The site says plainly that it is a class project prototype and not medical advice. No number is shown unless it comes from a committed metrics file, named on the page. Processing is described as it is: the photo is read by a model on the same computer, nothing goes to external services, results are stored encrypted for the session, one button deletes everything. When Tamil or Hindi is selected, every page shows the note "Machine-drafted translation, not yet checked by a native speaker." in that language. The word "safe" appears only in the negated form "This does not mean they are safe." (the same form as the backend template; tested, guardrail scan passes by negation).

## Strings pipeline
All user-visible text is `ui.*` in `data/templates/templates.json` (en, ta, hi; ta and hi `draft_unreviewed`), created by `scripts/add_phase6a_templates.py`, exported to `frontend/src/i18n/strings.generated.json` by `scripts/export_ui_strings.py` (a test fails if it is stale), and reviewed through `data/templates/review_sheet_phase6a_new.csv`.

## No network at runtime
Fonts and photographs are self-hosted; no CDN, analytics or third-party script. localStorage holds only `language` and `calm`. No cookies are set by the frontend.

## What was built and measured (Phase 6a)
Routes: `/` landing (hero with a 15-tile drifting mosaic, steps strip, "why you confirm first" figure, languages block, privacy band, limits notice, testing teaser), `/how-it-works` (SVG diagram shown from 48 rem up, numbered list below), `/privacy` (live consent notice, clear message when the backend is unreachable, retry), `/start` (placeholder), 404.
- **Tests**: vitest 18 (API client, strings, source scan, particle and pointer logic); Playwright 32 (21 site, 10 axe, 1 perf); contrast 36 of 36 pairs pass; backend 855.
- **axe** (wcag2a, 2aa, 21a, 21aa, 22aa) on all 5 routes in en and ta: 0 violations of any impact. Axe cannot judge reading order, focus return or Tamil/Hindi quality; those were checked only through the keyboard tests and screenshots.
- **Frame cost** (headless Chromium, production build, `?perf=1`): 60 particles, work per frame average 0.29 ms, p95 0.50 ms; frame interval average 16.67 ms, p95 16.8 ms (60 fps pacing). Headless is not a real GPU or display, so treat this as a CPU-cost figure.
- **Build**: main JS 479 KB raw, 143 KB gzip; GSAP and ScrollTrigger load on demand (27 KB and 17 KB gzip) only when motion is allowed; CSS 34 KB raw, 8.5 KB gzip; fonts: all subsets are in `dist` (328 KB woff2) but a page downloads only the scripts it shows; photos: 4 images in 800/1400/2000 px WebP and JPEG, largest files 105 to 290 KB (the leaves JPEG is above the 250 KB target because it is very detailed).
- **No WebGL** anywhere (test scans the bundle). **GPU memory**: nvidia-smi showed 1884 MiB before and 1770 MiB after the page ran in headless Chromium: not measurable (other applications dominate; headless rasterises on the CPU).
- **Known limits**: the how-it-works diagram is hidden under 48 rem (the list carries the content); the full-page screenshots show the particle canvas only in the first screen because it is a fixed layer; Tamil and Hindi headings use smaller display sizes than English because the glyphs are wider; 6 of 10 photo themes are placeholders.

## Flow patterns (Phase 6b)
Routes: `/start`, `/consent`, `/upload`, `/d/:id/processing`, `/d/:id/review`, `/d/:id/result`, `/d/:id/schedule`, `/d/:id/summary`, `/documents`. Every flow page is a `FlowPage` (`src/flow/FlowPage.tsx`): a progress strip (consent, photo, check, results, schedule; current step by number, text and `aria-current`, never colour alone), a session and consent gate (loading, offline with retry, expired with "Start again", redirect to consent), and focus moved to the page `h1` on arrival. State is `FlowProvider` (reducer, in memory only): session, documents, problem, dirty flag and the photo object URL. A language change is sent to the server (`POST /sessions`) so server-written text follows it.
- **Review (the central screen)**: photo with zoom and pan beside the list on wide screens (toggle on narrow ones; keyboard: arrows, plus, minus, 0). One card per medicine, in the same order as the paper: the name as written, the verbatim source quote (monospace, terracotta rule), strength, dose, how often, duration; a review badge (must confirm = filled terracotta with alert icon and a thick left rule; note = tinted info; nothing flagged = check), the backend's reasons as sentences, then a radio group of the API's allowed actions. Each acknowledgement flag has its own checkbox with the backend sentence; the card's button stays disabled and says what is still needed. The formulary picker is an ARIA combobox (typeahead, 20 results, brands + generic + strengths in every option, nothing preselected). A sticky summary bar counts what is still to confirm and saves the whole set. After saving, a panel shows per medicine whether it will be looked up for interactions and whether it has a schedule.
- **Results**: language tabs (a language is started on first selection and polled), banner, medicines with confirmation labels, advice/warnings with trust chips (draft translation, checked by software only, original text), interaction cards (level icon + text + colour, medicine names, source label, backend message), one aggregated not-checked line, attribution and brand-matching notices. A print stylesheet hides navigation and ambient layers.
- **Schedule**: today's slots with Taken and Skipped toggles (`aria-pressed`) and Undo, a 7-day strip, per-medicine time editor (1 to 6 times), the not-scheduled list with the backend reasons, and a plain statement that no reminders or notifications exist.
- **Components added**: `Dialog` (native `<dialog>`: focus trap, Escape, focus return), `DeleteControl`, `Progress`, `ProblemNotice` (icon + text, takes focus), `FormularyPicker`, `PhotoViewer`, `MedicineCard`, `ScheduleFields`, `AddMedicine`.
- **Errors**: backend message first (`GET /strings` `error.<code>`, `job.failed.<code>`), client wording (`ui.flow.problem.*`) only as fallback; always an icon plus text; `role="alert"` and focus.
- **Tests**: `e2e/mock.ts` is a stateful fake API that validates every request body against `docs/openapi.json`; `e2e/flow.spec.ts` covers the flow; `e2e/flow-a11y.spec.ts` runs axe on 14 flow states in en, ta and hi (0 violations); `e2e/live/` is the live run with the real model.

## Icon audit (Phase 6c-3)
Method: every route screenshotted at 1280 px (en) and read against the rule "status and severity are icon + text + colour; headings and list items that name a kind of thing carry an icon". Icon budget: 6 new icons at most; used 6 (`menu`, `still`, `zoomin`, `zoomout`, `chevron`, `reset`). Set total 26, all tested (`icons.test.ts`, `e2e/icons.spec.ts`).

| Location | Before | Decision |
|---|---|---|
| Header: menu button | did not exist | `menu` / `close` icon + the word "Menu" |
| Header: calm toggle | wave icon + words | icon-only on the desktop row (`wave` off, `still` on; words stay for screen readers, tooltip and the menu panel) |
| Header: delete | trash + words | icon-only below 90 rem (name kept for screen readers and tooltip), words from 90 rem and in the menu |
| Header: language | icon + names | unchanged (icon hidden on the compact row; names are the content) |
| Landing: three steps strip | icon per step | unchanged |
| Landing: why you confirm first (figure) | check on the good box only | `alert` added on the misread box (the bad side was colour and dashes only) |
| Landing: languages block | chips with icon | unchanged |
| Landing: privacy list | lock, clock, trash | unchanged |
| Landing: limits list | alert icon on the notice, numbered list | unchanged (numbers are the marker) |
| Landing: mosaic tiles | decorative icon on some tiles | unchanged: tiles are texture on purpose; no icon added to every tile |
| How it works: diagram outcomes | text and colour only | `alert` on "Interaction found", `help` on "Could not check" |
| How it works: numbered list | numbers only | step icon per heading (camera, document, check, language, search) |
| Consent: notice items | numbers only | icon per notice item id (document, lock, clock, calendar, trash, shield, info, language, circle-alert) |
| Consent purposes | checkboxes with Required and Optional tags | unchanged |
| Upload: dropzone, guidance | document and camera icons, notice icon | unchanged |
| Processing: stages and errors | clock, check, leaf per stage; alert in problems | unchanged |
| Review: cards and badges | icon + text per review level, reasons with icon | unchanged (the layout is redesigned in 6c-5) |
| Result: section headings | text only | `IconHeading`: pill, calendar, leaf, alert, shield, search |
| Result: medicine lines, warning lines | rule colour only | `pill` on medicine lines, `alert` on warning lines |
| Result: interaction cards, chips | severity icon + text + colour | unchanged |
| Schedule: taken and skipped | icon appears when selected | unchanged (state is icon + text + fill) |
| Summary: headings | text only | `IconHeading` (pill, calendar, circle-alert, shield) |
| Documents: state per document | plain text | `Tag` with a state icon (clock, circle-alert, alert, close) |
| Documents and 404: empty and not-found text | text only | `document` and `search` icons beside the sentence |
| Delete dialog | trash on the confirm button, alert on failure | unchanged |

## Header, review page, photographs (Phase 6c)
- Header: row layout from 70rem (96rem Tamil; 6d: the Testing link made the row wider), calm toggle icon-only on the row, delete label from 90rem; below that a single-DOM `#site-menu` disclosure keyed to the route (closes on navigation).
- Review page: `.review-shell` = sticky summary bar (counts, jump to next card needing a check, save) + photo pane + numbered cards. Statuses attention / checked / no action, always icon + text + colour. Phones: bar fixed at the bottom, photo opens in a full-screen dialog.
- Photographs: leaves, breakfast, stethoscope, water, linen, clipboard in the hero mosaic (decorative, empty alt); phone, notebook, pillbox on the landing steps; blister under "why you confirm first"; clipboard in the privacy band. Credits (photographer, licence, source link from `photos.manifest.json`) in a footer `<details>`.

## Sample mode and testing page (Phase 6d)
- Sample (`/demo`, docs/DEMO.md): same components on recorded responses. Label strip (dashed terracotta outline = "not real", same idea as the draft tag) is part of the sticky header on every demo page with a "Leave the sample" link; header "Sample" tag (hidden on phones, where the strip says it); one-line "nothing to delete" note on each page; a note above the photo viewer says the photo is a deliberately blurry scan.
- Testing page: group headings, one shared data line per group, table on wide screens, one card per figure below 48rem; caveat marked with a terracotta rule; Limits in an important notice.
