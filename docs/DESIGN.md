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
No claim of accuracy, speed or "AI-powered diagnosis". The words safe, safely, guaranteed, accurate, certified, clinically validated and doctor-approved are never used in the English copy (tested). Nothing implies a pharmacist, doctor or native speaker reviewed anything. The site says plainly that it is a class project prototype and not medical advice. No number is shown unless it comes from a committed metrics file, named on the page. Processing is described as it is: the photo is read by a model on the same computer, nothing goes to external services, results are stored encrypted for the session, one button deletes everything. When Tamil or Hindi is selected, every page shows the note "Machine-drafted translation, not yet checked by a native speaker." in that language. Because the owner's rule bans the word "safe", the "not checked never means safe" statement is worded as "not a sign that the medicines go well together".

## Strings pipeline
All user-visible text is `ui.*` in `data/templates/templates.json` (en, ta, hi; ta and hi `draft_unreviewed`), created by `scripts/add_phase6a_templates.py`, exported to `frontend/src/i18n/strings.generated.json` by `scripts/export_ui_strings.py` (a test fails if it is stale), and reviewed through `data/templates/review_sheet_phase6a_new.csv`.

## No network at runtime
Fonts and photographs are self-hosted; no CDN, analytics or third-party script. localStorage holds only `language` and `calm`. No cookies are set by the frontend.
