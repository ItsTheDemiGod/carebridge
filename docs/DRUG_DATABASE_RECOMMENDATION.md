# Drug interaction database recommendation

Research date: 2026-10-04. Facts below were read from the official pages cited. Nothing was downloaded.
Where a page could not be read (some NLM pages returned HTTP 403 to the fetch tool), that is stated.

## Recommendation (short)

1. **Interaction pairs: DDInter** (free CSVs, CC BY-NC-SA 4.0, covers drug-drug interactions with risk levels). Fine for a non-commercial class project.
2. **Indian brand to generic mapping: our own `data/reference/formulary.json`**, extended as needed. No public database covers Indian brands well.
3. **Name normalisation: not needed in Phase 4** if we map brand to generic through the formulary first. RxNorm API is an optional later add-on.
4. **Do not use** DrugBank (academic downloads paused, NC licence) or the retired RxNav interaction API. openFDA labels and WHO ATC are secondary at most.
5. **Safety stance:** the interaction check is a deterministic table lookup. The LLM never decides whether an interaction exists. A pair not found means "not checked / not in our database", never "safe".

## Comparison

| Source | What it provides | Licence / student use | Drug-drug interactions? | Indian brands | Access format | Key risks |
|---|---|---|---|---|---|---|
| **RxNorm / RxNav** | US normalised drug names and RxCUI identifiers; name-to-ID functions (`findRxcuiByString`, `approximateTerm`) | RxNorm API needs no licence; full downloads need a free UMLS licence. NLM attribution required. Free for students. | **No longer via RxNav.** The Drug Interaction API and Interactions tab were discontinued on **2 Jan 2024**. | Poor: US products only. | REST API; monthly download | US-centric; the interaction API is gone (see below) |
| **openFDA drug labels** | US SPL drug label text as JSON, including free-text interaction sections | CC0 public domain; attribution requested; no warranty | Only as unstructured label text, not structured pairs | None (US labels) | REST JSON API | Free text needs parsing (an LLM would be tempting, which we must avoid); FDA says labels are not verified for medical decisions; US-only |
| **DDInter** | 236,834 DDI associations across 1,833 approved drugs, with risk levels, mechanism and management notes (per its homepage) | CC BY-NC-SA 4.0: personal, non-commercial, scholarly use allowed; share-alike if redistributed. Fine for a class project, **not** for a commercial product. | **Yes**, this is its purpose | None found on the download page; international generic names | 8 CSV files, one per ATC group (A, B, D, H, L, P, R, V), 0.3 to 3.9 MB each | Homepage shows v1.0, updated Sept 2020 (may be stale); CSV columns not visible without downloading; ATC groups C, G, J, M, N are not in the 8 listed files, so we must check coverage for our formulary (e.g. cardiovascular, antibiotics) before relying on it |
| **DrugBank** | Rich drug data incl. interactions | Most datasets CC BY-NC 4.0. Academic licence is free for students but **"all Academic DrugBank dataset downloads are temporarily paused"**. Only Vocabulary and Structures are CC0. | Yes, but not obtainable now | None found | XML / CSV | Download unavailable; licence paperwork; NC restriction |
| **WHO ATC** | Drug classification codes and DDDs, for categorisation | Copyright WHO Collaborating Centre, Oslo. Attribution required; the copyright page forbids "copying and distribution for commercial purposes" and "changing or manipulating the material". Commercial/software licensing not stated on the page. | No | None | Web index; paid/licensed downloads | Licence ambiguity for embedding the full index; use only codes for our own drugs, with attribution |

### Is the RxNav interaction API still available?

**No.** NLM's own RxNav FAQ states: "RxNav's drug/drug interaction features were discontinued on January 2, 2024. However, the sources from which RxNav drew may remain available." Those sources were the ONCHigh list and DrugBank's interaction data. The other RxNorm APIs remain available. No replacement or reason is given on the FAQ page. The API reference page itself returned HTTP 403 to our tool, so the FAQ is the confirming source.

## Plan: mapping Indian brand names to generics

1. Keep the formulary as the single source: `brand_names` to `generic_name` (case-insensitive match, strip "Tab/Cap", strength, and punctuation first).
2. Phase 2 extraction outputs the name as written. A deterministic lookup then resolves brand to generic. If both are written, check they agree (the dataset validator already does this).
3. Unknown name: do not guess. Flag "medicine not recognised, interaction check skipped" and show it to the user.
4. Extend the formulary only with pharmacist-reviewed entries. Its `verification_status` is currently `unverified_requires_pharmacist_review`; a pharmacist or clinician should review it before any real use.
5. Combination products (e.g. amoxicillin + clavulanic acid) are stored as a combined generic name; Phase 4 must split them into components before the interaction lookup.

## Plan: Phase 4 interaction checking without LLM memory

1. After Phase 2, every medicine is resolved to a generic via the formulary.
2. Build a local lookup table `generic_a, generic_b -> severity, mechanism text` from the DDInter CSVs, restricted to the generics in our formulary (keeps it small and reviewable). Keep the DDInter attribution and CC BY-NC-SA notice with it.
3. For each pair of the patient's medicines, look up the table. Output only what the table says. The LLM may reword the stored text into plain EN/TA/HI but is not given the chance to add or remove interactions; a check step compares the reworded text with the stored text.
4. Report coverage honestly: "N of M pairs checked; these medicines are not covered." Never state "no interactions".
5. Unit tests with known pairs from the table, plus tests that unknown pairs return "not checked".
6. Always end with "confirm with your doctor or pharmacist". Show the data source and its date.

## Needs your decision (Phase 4 prep, nothing downloaded yet)

- Approve downloading the DDInter CSVs (total about 10 MB; well under what I would call "large") so we can check whether they cover our 66 formulary drugs and which columns they contain. If coverage is poor, the fallback is a small hand-curated, pharmacist-reviewed table for our formulary.

## Sources

- RxNav FAQ (discontinuation): https://lhncbc.nlm.nih.gov/RxNav/information/FAQs.html
- RxNorm API (no licence needed): https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html
- RxNorm terms of service: https://www.nlm.nih.gov/research/umls/rxnorm/docs/termsofservice.html
- openFDA terms: https://open.fda.gov/terms/
- openFDA drug label API: https://open.fda.gov/apis/drug/label/
- DDInter home: https://ddinter.scbdd.com/
- DDInter terms: https://ddinter.scbdd.com/terms/
- DDInter downloads: https://ddinter.scbdd.com/download/
- DrugBank licence/releases: https://go.drugbank.com/releases/latest#open-data
- WHO ATC/DDD index: https://atcddd.fhi.no/atc_ddd_index/
- WHO ATC copyright: https://atcddd.fhi.no/copyright_disclaimer/

Note: the summaries of these pages were produced by a fetch tool, not read in full by hand; re-check licence wording on the live pages before publishing or redistributing anything.
