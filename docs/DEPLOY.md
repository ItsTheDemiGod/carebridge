# Deploying the hosted sample (GitHub Pages)

**Expected address:** https://itsthedemigod.github.io/carebridge/ (GitHub lowercases the user name in the domain; the site is served under the base path `/carebridge/`).

## What is deployed
Only the **pre-recorded sample site**: the landing page, How it works, Privacy (a static copy of the consent notice made at build time), How we tested it, the sample under `/demo/*`, a 404 page and a "sample only" page for every route of the real flow (`/start`, `/consent`, `/upload`, `/documents`, `/d/*`). It is a static folder (`frontend/dist-demo`, about 9 MiB, 88 files: scripts, styles, self-hosted fonts and photographs, the sample image, the recorded fixtures). The page code makes **zero requests** to any `/api` path or to any other host.

## What is NOT deployed
The backend, the local model, the real upload flow, any session or database, `.env` files or keys, the DDInter raw data and derived store (only the attributed excerpt of at most six pairs inside the recorded fixtures), the raw full-size photographs (`photos/raw` is removed from the output by `frontend/scripts/make-404.mjs`), evaluation results, the dataset, and anything private. The real flow runs only on the owner's computer.

## How the workflow works (`.github/workflows/pages.yml`)
Triggers: a push to `master`, or "Run workflow" by hand. Permissions: `contents: read`, `pages: write`, `id-token: write` (nothing else); no repository secrets are used. Official actions only, pinned to major versions (`actions/checkout@v4`, `setup-node@v4`, `configure-pages@v5`, `upload-pages-artifact@v3`, `deploy-pages@v4`). A concurrency group stops two deployments from overlapping. Steps in the `build` job (working directory `frontend`): `npm ci` (from `package-lock.json`), `npm test` (vitest), `npm run build:demo`, upload `frontend/dist-demo`. The `deploy` job publishes it. The workflow never starts the backend, Playwright, Ollama or anything that needs a secret. `scripts/check_workflow.py` (stdlib; tested in `backend/tests/test_pages_workflow.py`) checks these rules.

`npm run build:demo` = type-check, `vite build --mode pages --outDir dist-demo` (base `/carebridge/`; set `PAGES_BASE` to change it), then `scripts/make-404.mjs` (copies `index.html` to `404.html` because Pages has no single-page-app fallback, and removes `photos/raw`). In this mode the real-flow pages are replaced by a stub module and are not bundled.

## One-time setup on GitHub
Repository **Settings, Pages, Source: GitHub Actions**. Then push to `master` (or run the workflow by hand). The first run creates the `github-pages` environment.

## Checks before publishing
- `python scripts/scan_repo_history.py --tree frontend/dist-demo` on the built folder: 0 secret findings, 0 private paths, 0 personal-data findings, 88 files, 9.4 MiB, no file over 5 MB.
- `npm run test:demo` (mocked Playwright against the built folder served like Pages under `/carebridge/`, no backend): routes in English, Tamil and Hindi, zero `/api` requests, deep links and reload, no overflow at five widths, axe on every route, assets 200, offline navigation, storage keys.
- A deep link such as `/carebridge/demo/review` is answered by `404.html` with HTTP status 404 (that is how Pages works); the page still renders and the browser logs one "404" line for that document. Assets never 404.

## Roll back
Revert the commit on `master` and push (the workflow redeploys the previous state), or switch Pages off: Settings, Pages, Source: None. Nothing else changes; the real app is not affected.

## Known risks
- `npm ci` on Linux uses a lockfile written on Windows. If an optional native package is missing from the lockfile the install step fails in the Actions log; nothing is deployed in that case.
- Tamil and Hindi text on the site is machine-drafted and unreviewed; the draft note stays on every page in those languages.
- The site is a recorded sample, not a live service. It is a class project prototype and not medical advice.
