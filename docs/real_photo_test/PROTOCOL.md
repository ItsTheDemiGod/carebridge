# Real-photo test: instructions for the owner (Phase 7c)

**Purpose**: our "photo" and "poor" test images are simulations. This test measures how the system copes with REAL phone photos of printed synthetic documents, and how far the simulations are from them. 25 photos in total. Everything photographed is fictional text on paper; no person, no real medical paper, no face, no screen with personal data may appear in any photo.

## 1. Print
Print `docs/real_photo_test/print_pack.pdf` on plain white A4, black ink, single sided, 100 percent scale ("actual size", no "fit to page"). Five pages, footers RP1 to RP5. Do not write on the pages. Keep two spare copies of RP1 if you want to crumple a page for condition E.

## 2. Photograph (one photo per page per condition)
| code | condition | how |
|---|---|---|
| A | daylight by a window | page flat on a table next to a window, daytime, no lamp, phone held about 30 cm above, whole page in view |
| B | room lamp at night | same, in the evening under an ordinary room lamp, no daylight |
| C | partial shadow | as A, but a hand or an object (cup, book) casts a shadow over part of the page |
| D | tilted | as A, but hold the phone or the page so the page is tilted about 15 to 20 degrees (not a straight top-down view) |
| E | crumpled or curved | the page crumpled and smoothed out, or curved like a page of an open book |

- **RP1 to RP4**: all five conditions A to E (20 photos). **RP5**: all five conditions as well (5 photos). Total 25.
- Name each file `RPn_X.jpg` (for example `RP2_C.jpg`). Exactly that pattern; the scorer refuses anything else.
- Phone camera: normal photo mode; NO filters, NO document-scan mode, NO beauty or HDR-enhancement extras, NO zoom crop; flash OFF for A to D, flash allowed for E. Keep the whole page inside the picture and keep the text readable by eye. Do not edit or crop the photos. JPEG is fine.
- Take one photo per cell; if a photo is unusable (page cut off, blurred beyond reading by eye), retake it once and keep only the retake.

## 3. Move the photos to the PC and save them
Copy the 25 JPEG files (cable, or a cloud folder without any editing) into `data/real_photos/` in this repository. That folder is gitignored; the file `data/real_photos/mapping.json` (made by `scripts/build_print_pack.py`) must stay there and must NOT be deleted. Remove the phone copies afterwards if you prefer; nothing here is personal.

## 4. Checklist
- [ ] 5 pages printed, none edited
- [ ] RP1 to RP5 each photographed under A, B, C, D, E (25 files named RPn_X.jpg)
- [ ] flash off for A to D; no filters, no scan mode, no crop
- [ ] no person or personal item in any photo
- [ ] files saved in `data/real_photos/` next to `mapping.json`
- [ ] the backend is running (`cd backend; .venv\Scripts\uvicorn app.main:app`) and the model is loaded (`ollama ps` shows at least 80 percent GPU)

## 5. Run (Phase 7c)
`backend\.venv\Scripts\python scripts\score_real_photos.py` then read `eval/results/real-photos-v1/metrics.md` and `comparison.md`. The scorer uploads only files named `RPn_X.jpg` with RPn in the mapping, deletes every session it creates, and prints only ids and counts. About 25 photos x 40 to 60 seconds.
