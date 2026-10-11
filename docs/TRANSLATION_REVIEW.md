# Translation review guide (Tamil and Hindi)

You are helping check how CareBridge explains a medical document in Tamil or Hindi. All documents are invented (synthetic); no real patient is involved. Nothing you see is medical advice. About 2 hours for one language.

## What you receive
Pick your language. You get two files:
- `review_ta.html` or `review_hi.html`: open it in any web browser (no internet needed). It shows 10 invented documents, line by line.
- `review_ta.csv` or `review_hi.csv`: open it in Excel or Google Sheets (File, Import, UTF-8). This is where you write your answers.
- If you also review the fixed sentences: `data/templates/review_sheet.csv` (see the last section).

## What the columns mean
- **Extracted English**: the line as read from the document (sometimes with doctors' shorthand).
- **English explanation**: the plain English version.
- **Shown to user**: the Tamil or Hindi text a patient would see. **This is the text you judge.**
- **Status**: `template` = a fixed sentence written by us; `verified` = our automatic checks accepted a machine-written text; `unverified` or `original_only` = the machine text was rejected, so the patient sees the original English with a notice. For rejected lines the grey text shows what the machine wrote; it is not shown to patients, but if it is good or bad tell us in the comment.
- **Judge**: what our checker said. You can ignore it while reviewing; it is there for us to compare.

## Your job, row by row
Read "Extracted English" and "Shown to user". Write ONE of these in the column `reviewer_verdict` (type it exactly):
- `correct`: the meaning is the same and the wording is natural and simple.
- `understandable_but_awkward`: the meaning is right but the wording is unnatural, too formal, or hard for an ordinary person. Put a better wording in `reviewer_comment`.
- `wrong_meaning`: something is changed, added or missing (a wrong body part, food or number; a missing "not"; a missing item). Say what is wrong in `reviewer_comment` (required).
- `unsafe`: a patient could be harmed or misled (for example a changed number, a reversed instruction, or advice that is not in the original). Say why in `reviewer_comment` (required).

Rows whose status is `unverified` or `original_only` show English on purpose; mark them `correct` if the notice is shown in good Tamil/Hindi, and use the comment for the grey text.

Things to look at: drug names and numbers must stay as in the original; sentences short and in everyday words; polite but plain; no wording that sounds like a doctor giving new advice.

## How to return it
1. Fill `reviewer_verdict` (and `reviewer_comment` where needed). Do NOT edit any other column.
2. Save as CSV (UTF-8) with a new name, for example `returned_ta_AB.csv`, and email it back with your initials.
3. It is fine to leave rows empty if you ran out of time; tell us how far you got.

## What we do with your answers
We run `python scripts/import_review_pack.py returned_ta_AB.csv --reviewer AB`. It refuses the file if a verdict is misspelled, a required comment is missing, a row was removed, or the shown text was edited, and tells us the row numbers. Otherwise it writes `docs/review_pack/results_<lang>.md` with counts per verdict and status and a list of every `wrong_meaning` and `unsafe` row. We then fix prompts, templates or rules; the results are the first real measure of Tamil and Hindi quality (until now only an automatic checker has looked at them).

## Reviewing the fixed sentences (template review sheet)
`data/templates/review_sheet.csv` has every fixed Tamil and Hindi sentence used for medicine lines and notices (108 rows). Words in curly brackets, such as `{name}` or `{n}`, are filled in by the program: **keep them exactly as they are** in any correction.
- `english`: the English original. `translation`: the current Tamil/Hindi draft.
- `reviewer_verdict`: same four words as above. If the draft is not `correct`, write the improved sentence in `reviewer_correction` (required for `wrong_meaning` and `unsafe`; a correction must contain exactly the same {placeholders}).
- Do not change `template_id`, `language` or `english`.
- Return the file; we run `python scripts/import_review_sheet.py returned.csv --reviewer AB`. It refuses the whole file and lists the bad rows if a placeholder was dropped, a template or language is unknown, or the English column no longer matches. Good rows are marked `reviewed` with your initials and the date.

Thank you. If anything is unclear, write it in the comment column.
