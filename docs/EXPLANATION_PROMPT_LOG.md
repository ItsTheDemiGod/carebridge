# Explanation prompt log (Phase 3)

Rules: at most TWO revisions of the narrative prompts, driven only by DEV-set failures, general rules only (no examples copied from dev documents). Dev split, condition `clean`, 20 documents, 135 free-text lines (60 advice, 21 follow-up, 54 warning). Model `qwen3-vl:8b-instruct`, text only, temperature 0, seed 42. The same model writes and judges, which weakens the judge.

## v1 (`backend/app/prompts/narrative_v1/`)
Prompts A (simplify), B (translate), C (back-translate), D (judge). Results in `eval/results/phase3-dev-clean-prompt-v1/` (its metrics.json still carries the original run id `phase3-dev-clean`).

Failure analysis of the first v1 run:
1. Tamil translation of a whole document failed with `context_truncated` for 9 of 20 documents (53 Tamil lines without any text). Cause: a repetition loop on a line full of abbreviations until `num_predict` (3000 tokens, about 80 s). This is a batching bug, fixed in code, not in the prompt: Tamil is translated in chunks of 4 lines, a failed chunk is retried line by line (only the looping line is lost), and deterministic failures are cached so a rerun does not repeat the 80 s.
2. After that fix the remaining failures are meaning errors that the judge catches: wrong word for a body part, food or symptom (for example a symptom word replaced by an unrelated noun), and omitted items in a list.

## v2 (`narrative_v2/`, default)
Only prompt B changed. Three general rules added: translate each item on its own, one sentence at a time, keep the length, never repeat a word; keep abbreviations, shorthand and medical codes in Latin letters; if unsure of the exact word for a body part, food, symptom or medical term, keep the English term in Latin letters instead of choosing another word.

| dev, clean, all 135 lines | v1 | v2 |
|---|---|---|
| English verified | 1.000 | 1.000 |
| Tamil verified | 0.200 | 0.274 |
| Hindi verified | 0.696 | 0.763 |
| Tamil lines with no model text (loops) | 18 | 0 |
| Tamil judge: contradicts / omits / adds | 45 / 31 / 11 | 50 / 40 / 7 |
| Hindi judge: contradicts / omits / adds | 18 / 14 / 6 | 7 / 15 / 9 |
| lines verified in all three languages | 0.156 | 0.237 |
| failed model calls | 5 (after the chunking fix) | 0 |

v2 kept. The second allowed revision was NOT used: the remaining Tamil failures are mostly `contradicts` and `omits_information`, which look like a capability limit of an 8B model in Tamil rather than something prompt wording fixes, and a further revision would risk overfitting the 20 dev documents.

## Reading the numbers
- English is 100% verified because the simplifier returns the source text unchanged for 64 of 135 lines and only lightly rewords the rest; readability barely changes (Flesch-Kincaid median 3.65 to 2.88). The English path therefore proves the verification layer more than it proves simplification.
- Tamil falls back to the original English text for 72.6% of free-text lines, Hindi for 23.7%. This is the safe outcome by design, but it means the Tamil experience is mostly original English with a notice until a stronger model or a native-speaker pass exists.
- No Tamil or Hindi string has been reviewed by a native speaker. The judge is the same model that wrote the text; native review in Phase 7 is the real check.

## Phase 3e: no revision
The stress set (eval/results/stress-v1) showed no failure that a general prompt rule fixes: the English simplifier changed every hard line (FK median 13.9 to 8.3), 14 of 15 verified, none lost or added a fact according to the judge, and the judge detected 19 of 20 wrong English candidates. The failures are (1) a deterministic regex (`you have` flagged as a diagnosis in "if you have chest pain"), which is a code rule, not a prompt, and (2) Tamil back-translation noise. The second allowed revision remains unused.

## Phase 4-0: conditional "you have" check
**Change** (`services/verification.py`, `_flagged`): the `diagnosis` forbidden-additions rule no longer fires when "you have" (or may/might/could have, suffer from) sits in a conditional clause: `if`, `when`, `whenever`, `unless` or `in case` earlier in the same clause (clauses end at . ; : ! ? ,) with at most three words between. "You have an infection." and "You have diabetes." are still flagged. Tests: `tests/test_you_have.py`. Source-side check unchanged.
**Re-run from cache only (no model call)**: `stress-v1b`, `phase3e-dev-clean-b`.
| | before (stress-v1) | after (stress-v1b) |
|---|---|---|
| English false-reject | 1/20 (0.05) | 0/20 (0.00) |
| Tamil false-reject | 3/6 (0.50) | 2/6 (0.33), remaining 2 are judge verdicts `adds_information` |
| Hindi false-reject | 1/6 (0.17) | 0/6 (0.00) |
The wrong-item results are unchanged: no wrong stress item newly passes (only the earlier miss en-w17, item_merged, is still verified; Tamil and Hindi: 0 missed).
**Dev (phase3e-dev-clean vs -b)**: verified shares identical (no dev line used the rule): en 1.00 for advice/follow_up/warning; ta 0.274 (advice 0.40, follow_up 0.143, warning 0.185); hi 0.763 (advice 0.867, follow_up 0.762, warning 0.648).
