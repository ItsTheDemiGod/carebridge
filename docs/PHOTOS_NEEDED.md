# Photographs still needed

Four of ten themes were obtained (see `assets/ATTRIBUTION.md`): foil blister pack, green leaves, linen texture, a tablet in a glass of water. Wikimedia Commons began answering with `429 Too Many Requests` during the search, so the search was stopped rather than pushed. The site shows designed placeholder tiles for anything missing, so nothing is broken.

## How to add one
1. Save the file as `frontend/public/photos/raw/<target name>.jpg` (the `raw/` folder is not committed).
2. Add an entry for it in `assets/photo_sources.json` (source URL, photographer, licence, date fetched, optional crop).
3. Run: `backend\.venv\Scripts\python scripts\prepare_photos.py`
   It writes 800, 1400 and 2000 px WebP and JPEG versions, strips metadata, updates `frontend/src/photos.manifest.json` and `assets/ATTRIBUTION.md`.
4. To use a photo in the hero or the steps, change its name in `components/Mosaic.tsx` or `pages/LandingPage.tsx`; alt text strings `ui.photo.*` already exist for all ten themes.

## Rules for every photograph
No recognisable faces. No brand logos. Nothing readable (drug names, barcodes, handwriting). Licence must be CC0, public domain, or CC BY (attribution recorded), or an Unsplash / Pexels file downloaded from a direct link with no login. At least 2000 px wide.

## Missing themes
| target filename (in `frontend/public/photos/raw/`) | search terms | minimum size |
|---|---|---|
| `pillbox.jpg` | weekly pill organiser, pill box days of week, hands (no faces) | 2000 px wide |
| `notebook.jpg` | open notebook pen cup of tea, journal tea desk | 2000 px wide |
| `breakfast.jpg` | breakfast table morning light, no people | 2000 px wide |
| `phone.jpg` | smartphone on wooden table screen off, top view | 2000 px wide |
| `stethoscope.jpg` | stethoscope on desk top down, no people | 2000 px wide |
| `clipboard.jpg` | clipboard papers from above, illegible text | 2000 px wide |

Candidates that were looked at and rejected: the printed side of the blister pack photograph (readable drug name and barcodes; only the empty foil side is used) and a restaurant table photograph with a wine glass and part of a person.


## Status after Phase 6c-4
All ten themes are obtained and placed (hero mosaic: leaves, breakfast, stethoscope, water, linen, clipboard; steps: phone, notebook, pillbox; why you confirm first: blister; privacy: clipboard). Checked in treated screenshots: the pink and blue pillbox and the breakfast photo sit calmly in the duotone; the stethoscope crop shows no print; the clipboard shows no readable text; no faces and no brand names. The pillbox shows partial weekday letters on its lids ("TUE"), which is not drug information. The 6a alt strings `ui.photo.pillbox` ("Hands holding...") and `ui.photo.water` ("on a saucer") describe photographs that were not the ones obtained; they are left unchanged for the reviewers and the pages use `ui.photo.pillbox_b`. No photograph is used on the 404 page or the empty states (a picture there would add weight without helping).
