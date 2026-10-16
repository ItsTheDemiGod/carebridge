# Formulary verification status

`data/reference/formulary.json` keeps `verification_status: unverified_requires_pharmacist_review`. **No formulary row is marked checked.** This file records what could be verified from official sources on 2026-10-16 (author check, not a pharmacist review). Nothing here changes the app.

**Brand-to-generic mapping (Indian brands such as Glycomet, Dolo, Telma) could not be verified from any official source reached; every brand mapping remains `unverified_prototype`.** The app shows this in the interaction notice.

Method: for each generic, openFDA drug-label search (`openfda.generic_name`, up to 25 labels, https://api.fda.gov/drug/label.json). Result `name+route ok` = at least one US label exists for that generic and its route list includes the formulary route. A strength counts as seen when the same number and unit appears anywhere in those labels' strength, supply or description text; this is a weak test (the strength may belong to another dosage form), so it supports 'exists' and does not confirm the exact product. Strengths not seen are listed. Other sources: WHO ATC index, EMA Galvus product information, HPRA Motilium leaflet.

| generic | what was verified | source | result |
|---|---|---|---|
| Metformin | name found (25 labels), route oral listed; strengths 500 mg, 850 mg, 1000 mg seen | openFDA labels | name+route ok |
| Glimepiride | name found (25 labels), route oral listed; strengths 1 mg, 2 mg seen | openFDA labels | name+route ok |
| Gliclazide | WHO ATC index A10BB09 (sulfonylureas, oral). Not in openFDA (not US-marketed). Strengths 40/80 mg not verified. | https://atcddd.fhi.no/atc_ddd_index/?code=A10BB09 | partly verified |
| Sitagliptin | name found (25 labels), route oral listed; strengths 50 mg, 100 mg seen | openFDA labels | name+route ok |
| Vildagliptin | EMA Galvus SmPC: name, tablet form, 50 mg tablet confirmed (route oral by SmPC). | Galvus EPAR product information (EMA) | partly verified |
| Pioglitazone | name found (25 labels), route oral listed; strengths 15 mg, 30 mg seen | openFDA labels | name+route ok |
| Dapagliflozin | name found (25 labels), route oral listed; strengths 5 mg, 10 mg seen | openFDA labels | name+route ok |
| Empagliflozin | name found (13 labels), route oral listed; strengths 10 mg, 25 mg seen | openFDA labels | name+route ok |
| Amlodipine | name found (25 labels), route oral listed; strengths 2.5 mg, 5 mg, 10 mg seen | openFDA labels | name+route ok |
| Telmisartan | name found (25 labels), route oral listed; strengths 20 mg, 40 mg, 80 mg seen | openFDA labels | name+route ok |
| Losartan | name found (25 labels), route oral listed; strengths 25 mg, 50 mg seen | openFDA labels | name+route ok |
| Olmesartan | name found (25 labels), route oral listed; strengths 20 mg, 40 mg seen | openFDA labels | name+route ok |
| Ramipril | name found (25 labels), route oral listed; strengths 2.5 mg, 5 mg, 10 mg seen | openFDA labels | name+route ok |
| Enalapril | name found (25 labels), route oral listed; strengths 2.5 mg, 5 mg seen | openFDA labels | name+route ok |
| Metoprolol succinate | name found (25 labels), route oral listed; strengths 25 mg, 50 mg seen | openFDA labels | name+route ok |
| Atenolol | name found (25 labels), route oral listed; strengths 25 mg, 50 mg, 100 mg seen | openFDA labels | name+route ok |
| Bisoprolol | name found (25 labels), route oral listed; strengths 2.5 mg, 5 mg seen | openFDA labels | name+route ok |
| Carvedilol | name found (25 labels), route oral listed; strengths 3.125 mg, 6.25 mg, 12.5 mg seen | openFDA labels | name+route ok |
| Furosemide | name found (25 labels), route oral listed; strengths 20 mg, 40 mg seen | openFDA labels | name+route ok |
| Torsemide | name found (25 labels), route oral listed; strengths 10 mg, 20 mg seen | openFDA labels | name+route ok |
| Spironolactone | name found (25 labels), route oral listed; strengths 25 mg, 50 mg seen | openFDA labels | name+route ok |
| Isosorbide mononitrate | name found (25 labels), route oral listed; strengths 30 mg, 60 mg seen | openFDA labels | name+route ok |
| Atorvastatin | name found (25 labels), route oral listed; strengths 10 mg, 20 mg, 40 mg, 80 mg seen | openFDA labels | name+route ok |
| Rosuvastatin | name found (25 labels), route oral listed; strengths 5 mg, 10 mg, 20 mg, 40 mg seen | openFDA labels | name+route ok |
| Aspirin | name found (25 labels), route oral listed; strengths not seen: 75 mg, 150 mg | openFDA labels | name+route ok; some strengths not seen |
| Clopidogrel | name found (25 labels), route oral listed; strengths 75 mg seen | openFDA labels | name+route ok |
| Ticagrelor | name found (25 labels), route oral listed; strengths 60 mg, 90 mg seen | openFDA labels | name+route ok |
| Enoxaparin | name found; route INTRAVENOUS/SUBCUTANEOUS (formulary says 'injection', which is a form, not a route); 40 mg seen | openFDA labels | name ok; route field not comparable |
| Pantoprazole | name found (25 labels), route oral listed; strengths 20 mg, 40 mg seen | openFDA labels | name+route ok |
| Rabeprazole | name found (25 labels), route oral listed; strengths 20 mg seen | openFDA labels | name+route ok |
| Omeprazole | name found (25 labels), route oral listed; strengths 20 mg seen | openFDA labels | name+route ok |
| Esomeprazole | name found (25 labels), route oral listed; strengths 20 mg, 40 mg seen | openFDA labels | name+route ok |
| Famotidine | name found (25 labels), route oral listed; strengths 20 mg, 40 mg seen | openFDA labels | name+route ok |
| Domperidone | HPRA (Ireland) Motilium 10 mg film-coated tablets leaflet: name, 10 mg tablet, oral confirmed. | HPRA leaflet | partly verified |
| Ondansetron | name found (25 labels), route oral listed; strengths 4 mg, 8 mg seen | openFDA labels | name+route ok |
| Racecadotril | No official source reached; not in openFDA. | none | not verified |
| Lactulose | name found (25 labels), route oral listed; strengths not seen: 10 g/15 mL | openFDA labels | name+route ok; some strengths not seen |
| Paracetamol | openFDA name 'acetaminophen': FDA name for paracetamol; ORAL; 500/650 mg not found in the 25 labels read | openFDA labels | partly verified |
| Ibuprofen | name found (25 labels), route oral listed; strengths 200 mg, 400 mg seen | openFDA labels | name+route ok |
| Diclofenac | name found (25 labels), route oral listed; strengths 50 mg seen | openFDA labels | name+route ok |
| Aceclofenac | No official source reached; not in openFDA. | none | not verified |
| Amoxicillin | name found (25 labels), route oral listed; strengths 250 mg, 500 mg seen | openFDA labels | name+route ok |
| Amoxicillin + Clavulanic acid | openFDA name 'amoxicillin + clavulanate': both components found, ORAL; 625 mg (UK/India presentation) not found as written | openFDA labels | partly verified |
| Azithromycin | name found (25 labels), route oral listed; strengths 250 mg, 500 mg seen | openFDA labels | name+route ok |
| Cefixime | name found (8 labels), route oral listed; strengths 100 mg, 200 mg seen | openFDA labels | name+route ok |
| Cefuroxime | name found (25 labels), route oral listed; strengths 250 mg, 500 mg seen | openFDA labels | name+route ok |
| Cefpodoxime | name found (15 labels), route oral listed; strengths 100 mg, 200 mg seen | openFDA labels | name+route ok |
| Ciprofloxacin | name found (25 labels), route oral listed; strengths 250 mg, 500 mg seen | openFDA labels | name+route ok |
| Levofloxacin | name found (25 labels), route oral listed; strengths 250 mg, 500 mg, 750 mg seen | openFDA labels | name+route ok |
| Nitrofurantoin | name found (25 labels), route oral listed; strengths 100 mg seen | openFDA labels | name+route ok |
| Metronidazole | name found (25 labels), route oral listed; strengths not seen: 200 mg, 400 mg | openFDA labels | name+route ok; some strengths not seen |
| Mupirocin | name found (25 labels), route topical listed; strengths not seen: 2% | openFDA labels | name+route ok; some strengths not seen |
| Cetirizine | name found (25 labels), route oral listed; strengths 10 mg seen | openFDA labels | name+route ok |
| Levocetirizine | name found (25 labels), route oral listed; strengths 5 mg seen | openFDA labels | name+route ok |
| Montelukast | name found (25 labels), route oral listed; strengths 10 mg seen | openFDA labels | name+route ok |
| Salbutamol | openFDA name 'albuterol': FDA name for salbutamol; inhalation route listed; 100 mcg not found as written | openFDA labels | partly verified |
| Budesonide + Formoterol | openFDA name 'budesonide + formoterol': both components found, inhalation route; 200/6 mcg not found as written | openFDA labels | partly verified |
| Tiotropium | name found (6 labels), route inhalation listed; strengths 18 mcg seen | openFDA labels | name+route ok |
| Ambroxol | No official source reached; not in openFDA. | none | not verified |
| Prednisolone | name found (25 labels), route oral listed; strengths 5 mg, 10 mg, 20 mg seen | openFDA labels | name+route ok |
| Levothyroxine | name found (25 labels), route oral listed; strengths 25 mcg, 50 mcg, 75 mcg, 100 mcg seen | openFDA labels | name+route ok |
| Calcium carbonate + Vitamin D3 | No official source reached; combination supplement, not a regulated label in openFDA search. | none | not verified |
| Cholecalciferol | name found (25 labels), route oral listed; strengths not seen: 60000 IU | openFDA labels | name+route ok; some strengths not seen |
| Folic acid | name found (25 labels), route oral listed; strengths not seen: 5 mg | openFDA labels | name+route ok; some strengths not seen |
| Tamsulosin | name found (25 labels), route oral listed; strengths 0.4 mg seen | openFDA labels | name+route ok |
| Gabapentin | name found (25 labels), route oral listed; strengths 100 mg, 300 mg seen | openFDA labels | name+route ok |

Summary: 59 of 66 generics found in openFDA by name (4 of them under US names); 3 more (gliclazide, vildagliptin, domperidone) confirmed from WHO, EMA or HPRA; 4 not verified (racecadotril, aceclofenac, ambroxol, calcium carbonate + vitamin D3). Strengths and forms are only weakly checked. A pharmacist must still review brands, strengths, forms and routes.
