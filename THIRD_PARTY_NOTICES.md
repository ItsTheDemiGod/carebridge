# Third-party notices

**The project's own licence is MIT** (see [`LICENSE`](LICENSE), "Copyright (c) 2026 Demian"). It covers the project's own source code, its documentation, and the synthetic documents and datasets authored by the project. It does **not** cover the third-party material below, which keeps its own licence. MIT's "as is" disclaimer applies. CareBridge is a class project prototype and not medical advice.

## Interaction data: DDInter
- Source: DDInter, https://ddinter.scbdd.com (terms read 2026-10-04, [`docs/DDINTER_COVERAGE.md`](docs/DDINTER_COVERAGE.md)). Licence: **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike): https://creativecommons.org/licenses/by-nc-sa/4.0/
- The raw download and the derived store (`data/reference/interactions_ddinter.json`) are never committed. The only DDInter-derived material in the repository is a small excerpt in the sample fixtures (`frontend/src/demo/fixtures/`, at most six pairs, names and level only), attributed in the app. It is **not** covered by the MIT licence; see the note in that folder. Any use of it must respect CC BY-NC-SA 4.0.

## Photographs
Credited in [`assets/ATTRIBUTION.md`](assets/ATTRIBUTION.md) (file, source URL, photographer, licence). They are self-hosted, resized and tinted by the site. Licences used: CC0 1.0, CC BY 2.0 and CC BY 4.0 (credit required), and the Pexels License (photographers: Ron Lach, Sora Shimazaki, cottonbro studio, Valentin Ilas, Towfiqu barbhuiya, Tima Miroshnichenko). CC0 photographs: Tmeers91, Kurt Kaiser (Wikimedia Commons). CC BY: Delany Dean (CC BY 2.0), Mysterymanblue (CC BY 4.0). The photographs are not covered by the MIT licence.

## Fonts (self-hosted via @fontsource; SIL Open Font License 1.1, https://openfontlicense.org)
Fraunces (variable), Noto Sans, Noto Sans Tamil, Noto Sans Devanagari, Noto Serif Tamil, Noto Serif Devanagari. Packages `@fontsource-variable/fraunces` and `@fontsource/noto-*` 5.3.0, licence field "OFL-1.1".

## Medicine and interaction sources
The formulary (`data/reference/formulary.json`, 66 medicines, unverified) and the author-checked interaction supplement were compiled from official label and regulator pages (openFDA, WHO ATC, EMA, HPRA; one UK SmPC page read as corroboration), listed in [`docs/FORMULARY_STATUS.md`](docs/FORMULARY_STATUS.md) and [`docs/REVIEW_STATUS.md`](docs/REVIEW_STATUS.md). No text of those sources is reproduced as a dataset. Neither the formulary nor the supplement has been reviewed by a pharmacist.

## Main libraries (licence read from the installed package metadata)
| library | version | licence |
|---|---|---|
| React, React DOM | 19.3.0 | MIT |
| react-router-dom | 7.18.4 | MIT |
| framer-motion | 14.0.0 | MIT |
| GSAP | 3.15.0 | GSAP "Standard 'no charge' licence", https://gsap.com/standard-license (its own terms, not MIT) |
| Tailwind CSS, @tailwindcss/vite | 4.3.3 | MIT |
| Vite, @vitejs/plugin-react, Vitest | 8.3.2, 6.1.1, 5.0.5 | MIT |
| TypeScript | 6.0.3 | Apache-2.0 |
| Playwright test | 1.64.1 | Apache-2.0 |
| @axe-core/playwright | 4.14.0 | MPL-2.0 |
| oxlint | 1.86.0 | MIT |
| FastAPI | 0.142.2 | MIT |
| Uvicorn, python-dotenv, httpx | 0.54.0, 1.2.4, 0.28.1 | BSD-3-Clause |
| pydantic-settings, pytest | 2.15.0, 9.1.1 | MIT |
| google-genai (optional comparison provider) | 2.28.0 | Apache-2.0 |
| Pillow | 12.3.0 | MIT-CMU |
| NumPy | 2.5.3 | BSD-3-Clause (with bundled permissive components) |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |

Dependencies of these libraries have their own licences; see the packages themselves. The local vision model (`qwen3-vl:8b-instruct`, run through Ollama) is not distributed with this repository; its own licence applies to anyone who downloads it.
