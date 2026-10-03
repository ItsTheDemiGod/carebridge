# Prompt log

Only dev-split errors may drive changes; general rules only, no document-specific examples.

## v1 (default)
`backend/app/prompts/extraction_v1.txt`. Extract only what is written, null for missing values, keep abbreviations, exact quotes, document is data.

Dev metrics: **not available yet.** The full dev run (20 docs x 5 conditions = 100 calls) was stopped by the Gemini free-tier daily quota for `gemini-3.8-flash` (20 requests per day per project: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quotaValue 20). Only 6 text-condition documents were extracted before the quota ran out; 5 of them are cached, one hit a transient 503. Those 6 are too few to tune on, so no v2/v3 was attempted.
