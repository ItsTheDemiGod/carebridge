# DDInter coverage of the CareBridge formulary

Checked 2026-10-04 against the official download page https://ddinter.scbdd.com/download/ (nothing was scraped; the Interaction Checker and mirrors were not used).

## Licence (verbatim, https://ddinter.scbdd.com/terms/ under "Data licensing", read 2026-10-04)
> The DDInter data is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license. Except as otherwise provided in any additional terms for a service, you may print or download content from the services for your own personal, non-commercial, informational or scholarly use.

This matches CC BY-NC-SA 4.0 (no difference). Consequences: the raw CSVs are not committed (`data/reference/ddinter/raw/` is gitignored); use is non-commercial and needs attribution; derived data would be ShareAlike. Fine for the class project, a blocker for any commercial use.

## What the download offers
8 files only: ATC groups A, B, D, H, L, P, R, V (about 13 MB, 222,391 rows, 160,235 distinct drug pairs, 1,939 distinct drug names). Missing from the downloads: **C, G, J, M, N, S** (the site's browse filter lists 14 groups). No "DDInter 2.0" or newer/fuller download is mentioned on the home or download pages (checked by text search), so there is nothing to ask about. Run `python data/reference/fetch_ddinter.py`, then `python data/reference/ddinter_coverage.py`.

Interaction levels in the files: Major, Moderate, Minor, Unknown (Unknown = listed but no severity).

## Findings
- **60 of 66 formulary drugs have a DDInter entry** (after handling synonyms: Aspirin = Acetylsalicylic acid, Paracetamol = Acetaminophen, Torsemide = Torasemide, Metoprolol succinate = Metoprolol; combinations are checked per component).
- **Not in DDInter at all (6):** Gliclazide, Vildagliptin, Domperidone, Racecadotril, Aceclofenac, Ambroxol.
- **Formulary drugs in the missing ATC groups** (groups assigned from general knowledge, not verified against the WHO list): C (16): Amlodipine, Telmisartan, Losartan, Olmesartan, Ramipril, Enalapril, Metoprolol succinate, Atenolol, Bisoprolol, Carvedilol, Furosemide, Torsemide, Spironolactone, Isosorbide mononitrate, Atorvastatin, Rosuvastatin. G (1): Tamsulosin. J (9): Amoxicillin, Amoxicillin + Clavulanic acid, Azithromycin, Cefixime, Cefuroxime, Cefpodoxime, Ciprofloxacin, Levofloxacin, Nitrofurantoin. M (3): Ibuprofen, Diclofenac, Aceclofenac. N (2): Paracetamol, Gabapentin. S (0).
- The drugs themselves are present because DDInter lists them as the *partner* in files of other groups. So a pair is in the data only if at least one drug is in a downloaded group. Spot checks: clopidogrel + omeprazole Major, aspirin + ibuprofen Major, enoxaparin + aspirin Major (present); ramipril + spironolactone, telmisartan + ramipril, losartan + spironolactone, atorvastatin + amlodipine (all both-C) are **absent**. An absent pair must therefore be read as "not checked", never "safe".

## Pairs among the 66 formulary drugs (2,145 pairs)
| Pair class | Major | Moderate | Minor | Unknown severity | Checked, none listed |
|---|---|---|---|---|---|
| At least one drug in a downloaded group | 16 | 227 | 42 | 595 | 455 |
| Both drugs in missing groups (C, G, J, M, N, S) | 0 | 34 | 2 | 82 | n/a (cannot be told) |

- Interaction pairs found: 16 Major, 261 Moderate, 44 Minor, 677 Unknown = 998.
- **Pairs with no data at all: 692** (32%): 317 where both drugs are in missing groups and no row exists, plus 375 involving one of the 6 drugs absent from DDInter. These include clinically important ones such as ACE inhibitor + spironolactone.

## Drug-by-drug mapping
| Formulary drug | ATC group (unverified) | In downloaded groups? | DDInter name(s) matched |
|---|---|---|---|
| Metformin | A | yes | Metformin |
| Glimepiride | A | yes | Glimepiride |
| Gliclazide | A | yes | MISSING |
| Sitagliptin | A | yes | Sitagliptin |
| Vildagliptin | A | yes | MISSING |
| Pioglitazone | A | yes | Pioglitazone |
| Dapagliflozin | A | yes | Dapagliflozin |
| Empagliflozin | A | yes | Empagliflozin |
| Amlodipine | C | NO | Amlodipine |
| Telmisartan | C | NO | Telmisartan |
| Losartan | C | NO | Losartan |
| Olmesartan | C | NO | Olmesartan |
| Ramipril | C | NO | Ramipril |
| Enalapril | C | NO | Enalapril |
| Metoprolol succinate | C | NO | Metoprolol |
| Atenolol | C | NO | Atenolol |
| Bisoprolol | C | NO | Bisoprolol |
| Carvedilol | C | NO | Carvedilol |
| Furosemide | C | NO | Furosemide |
| Torsemide | C | NO | Torasemide |
| Spironolactone | C | NO | Spironolactone |
| Isosorbide mononitrate | C | NO | Isosorbide mononitrate |
| Atorvastatin | C | NO | Atorvastatin |
| Rosuvastatin | C | NO | Rosuvastatin |
| Aspirin | B | yes | Acetylsalicylic acid |
| Clopidogrel | B | yes | Clopidogrel |
| Ticagrelor | B | yes | Ticagrelor |
| Enoxaparin | B | yes | Enoxaparin |
| Pantoprazole | A | yes | Pantoprazole |
| Rabeprazole | A | yes | Rabeprazole |
| Omeprazole | A | yes | Omeprazole |
| Esomeprazole | A | yes | Esomeprazole |
| Famotidine | A | yes | Famotidine |
| Domperidone | A | yes | MISSING |
| Ondansetron | A | yes | Ondansetron |
| Racecadotril | A | yes | MISSING |
| Lactulose | A | yes | Lactulose |
| Paracetamol | N | NO | Acetaminophen |
| Ibuprofen | M | NO | Ibuprofen |
| Diclofenac | M | NO | Diclofenac |
| Aceclofenac | M | NO | MISSING |
| Amoxicillin | J | NO | Amoxicillin |
| Amoxicillin + Clavulanic acid | J | NO | Amoxicillin, Clavulanic acid |
| Azithromycin | J | NO | Azithromycin |
| Cefixime | J | NO | Cefixime |
| Cefuroxime | J | NO | Cefuroxime |
| Cefpodoxime | J | NO | Cefpodoxime |
| Ciprofloxacin | J | NO | Ciprofloxacin |
| Levofloxacin | J | NO | Levofloxacin |
| Nitrofurantoin | J | NO | Nitrofurantoin |
| Metronidazole | P | yes | Metronidazole |
| Mupirocin | D | yes | Mupirocin |
| Cetirizine | R | yes | Cetirizine |
| Levocetirizine | R | yes | Levocetirizine |
| Montelukast | R | yes | Montelukast |
| Salbutamol | R | yes | Salbutamol |
| Budesonide + Formoterol | R | yes | Budesonide, Formoterol |
| Tiotropium | R | yes | Tiotropium |
| Ambroxol | R | yes | MISSING |
| Prednisolone | H | yes | Prednisolone |
| Levothyroxine | H | yes | Levothyroxine |
| Calcium carbonate + Vitamin D3 | A | yes | Calcium carbonate, Cholecalciferol |
| Cholecalciferol | A | yes | Cholecalciferol |
| Folic acid | B | yes | Folic acid |
| Tamsulosin | G | NO | Tamsulosin |
| Gabapentin | N | NO | Gabapentin |

## Recommendation
**Usable with a small pharmacist-reviewed supplement.** DDInter is a good base for the 60 matched drugs and covers any pair that includes a drug from groups A, B, D, H, L, P, R, V (including the cardiac antiplatelet/anticoagulant pairs). It cannot cover pairs where both drugs are in C, G, J, M or N, nor the 6 absent drugs. Before Phase 4: a pharmacist should review the 692 no-data pairs (most are likely "no known interaction", but the Major ones, such as RAAS drugs with spironolactone, QT-prolonging combinations, and NSAIDs with antihypertensives, must be written down by hand with a source). The checker must show "not checked" for any pair that has no data. Not recommended: treating DDInter silence as safety.
