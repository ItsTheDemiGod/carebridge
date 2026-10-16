# Pharmacist review: instructions

CareBridge is a college project that explains discharge papers and checks medicines against each other. You are asked to check **safety content** in two spreadsheets. You are **not** asked to check translations (other reviewers do that), and nothing here is used with real patients.

## What you receive
Two CSV files (open them in Excel or Google Sheets; if accented letters look wrong, import the file as UTF-8):

1. `interactions_supplement_review.csv` - 16 drug pairs we drafted from official labels (FDA labels and EU product information). One row per pair.
2. `formulary_review.csv` - the list of 66 medicines the app knows: brand names, strengths, form and route. **This list was written for software testing and has never been verified**, so it also needs your check.

## Why the first sheet exists
The app looks up interactions in a free database (DDInter). That database is incomplete, so many pairs have no record. When a pair has no record, the app only says "we could not check this", never "safe". The 16 pairs in sheet 1 have **no record in that database**, but we found a statement in an official label. Until you review them, **the app ignores them**.

## Sheet 1: interactions
Columns already filled: `pair_id`, `drug_a`, `drug_b`, `proposed_severity`, `summary_en` (our one-sentence paraphrase), `source_url`, `source_section` (where to look; "also:" lists a second label), `status`.
`proposed_severity` is `unclassified` when the label gives no severity.

Please fill in, for every row:
- `reviewer_verdict` (required), one of:
  - `agree` - the interaction is real and our sentence is fair. (If proposed_severity says `unclassified`, you must also give `reviewer_severity`.)
  - `change_severity` - the interaction is real but the level is wrong or missing; give `reviewer_severity`.
  - `remove` - this pair should not be shown (wrong, not clinically meaningful, or misleading).
  - `needs_more_info` - you cannot decide; explain in `reviewer_comment`. The app keeps ignoring this row.
- `reviewer_severity`: `major`, `moderate`, `minor` or `unknown` (unknown = an interaction exists but its seriousness is not known). Leave empty if you agree with a given level.
- `reviewer_comment`: anything we should know (free text, optional but welcome).
- `reviewer_initials` and `review_date` (format `2026-10-20`) - required on every row.

Things to look at: Is the interaction real? Is the severity sensible? Does the one-sentence summary say only what the source supports and avoid advice? Where the source does not name a drug (for example it says "QT-prolonging medicines" or "potassium-sparing diuretics") and we applied it to a specific drug, is that fair?

## Sheet 2: formulary
Columns already filled: `generic_name`, `brand_names`, `strengths`, `form`, `route`, `status`. Please check that the brands are real Indian-market brands of that generic, and that strengths, form and route exist.
Fill in, for every row: `reviewer_verdict` (`agree`, `correct` or `remove`); `reviewer_correction` (required for `correct`: write the correct brands/strengths/form/route); `reviewer_comment` (optional); `reviewer_initials`; `review_date`.

## What the app never does
It never tells anyone to change a dose or stop a medicine, never says a combination is safe, and always tells people to ask their doctor or pharmacist. You do not need to review those messages; they are fixed text reviewed separately.

## Returning the files
Save both files as CSV (keep the file names, keep the column order, do not add or delete rows or columns) and email them back. A returned file is checked automatically; **the whole file is refused if any row has a missing verdict, a missing initials/date, an unknown pair, or a severity outside the list above**, and we will send it back with the row numbers to fix.

## Licensing note
Interaction levels come from DDInter (CC BY-NC-SA 4.0; non-commercial use with attribution). The 16 drafted pairs come from official labels only.
