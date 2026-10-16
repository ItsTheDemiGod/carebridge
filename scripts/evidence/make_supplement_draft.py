"""ARCHIVE of how data/reference/interactions_supplement.json was drafted (2026-10-16). Run once from the repo root; it REFUSES to overwrite an existing file
(the live file carries pharmacist verdicts). Sources: official label / regulator pages only, fetched 2026-10-16."""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "data" / "reference" / "interactions_supplement.json"
F = "https://api.fda.gov/drug/label.json?search=openfda.generic_name:"
U = {
    "enalapril": F + "%22enalapril+maleate%22+AND+openfda.brand_name:%22vasotec%22&limit=1",
    "ramipril": F + "ramipril&limit=1",
    "olmesartan": F + "%22olmesartan+medoxomil%22+AND+openfda.brand_name:%22benicar%22&limit=1",
    "losartan": F + "%22losartan+potassium%22+AND+openfda.brand_name:%22cozaar%22&limit=1",
    "telmisartan": F + "%22telmisartan%22+AND+openfda.brand_name:%22micardis%22&limit=1",
    "spironolactone": F + "%22spironolactone%22+AND+openfda.brand_name:%22aldactone%22&limit=1",
    "levofloxacin": F + "levofloxacin&limit=1",
    "ciprofloxacin": F + "ciprofloxacin+AND+openfda.route:ORAL&limit=1",
    "azithromycin": F + "azithromycin&limit=1",
    "ondansetron": F + "ondansetron&limit=1",
    "domperidone": "https://www.ema.europa.eu/en/documents/referral/domperidone-article-31-referral-annex-iii_en.pdf",
    "galvus": "https://www.ema.europa.eu/en/documents/product-information/galvus-epar-product-information_en.pdf",
}


def S(k, sec):
    return {"url": U[k], "section": sec}


K = "Aldactone label, 7.1 Drugs and Supplements Increasing Serum Potassium (ACE inhibitors and ARBs are listed as drugs that can raise potassium)"
RAS = "Using an ACE inhibitor together with an angiotensin receptor blocker generally should be avoided because of low blood pressure, high potassium and kidney changes."
QT = "Domperidone is not to be used with medicines that lengthen the heart's QT interval, and {d} is labelled as one that can do this."
ACE = "The vildagliptin product information says taking it with an ACE inhibitor such as {d} may raise the chance of angioedema (swelling of the face, lips or throat)."
ROWS = [
    ("Enalapril", "Spironolactone", "unclassified", "Both medicines can raise blood potassium, so taking them together can push potassium too high.",
     S("enalapril", "Vasotec label, 7 Drug Interactions: Agents Increasing Serum Potassium (potassium-sparing diuretics)"), [S("spironolactone", K)]),
    ("Ramipril", "Spironolactone", "unclassified", "Taking these together increases the chance of high blood potassium, which needs regular blood tests.",
     S("ramipril", "Ramipril capsules label, 7.1 Diuretics (names spironolactone)"), [S("spironolactone", K)]),
    ("Olmesartan", "Spironolactone", "unclassified", "Together they can raise blood potassium, so potassium may need to be monitored.",
     S("olmesartan", "Benicar label, 7.1 Agents Increasing Serum Potassium (names spironolactone)"), [S("spironolactone", K)]),
    ("Losartan", "Spironolactone", "unclassified", "Both can raise blood potassium, so using them together may cause too much potassium in the blood.",
     S("losartan", "Cozaar label, 7.1 Agents Increasing Serum Potassium (drugs that raise serum potassium)"), [S("spironolactone", K)]),
    ("Telmisartan", "Spironolactone", "unclassified", "Both can raise blood potassium, so using them together may cause too much potassium in the blood.",
     S("telmisartan", "Micardis label, 7.1 Agents Increasing Serum Potassium (drugs that raise serum potassium)"), [S("spironolactone", K)]),
    ("Telmisartan", "Ramipril", "unclassified", "The ramipril label says this pair is not recommended because it adds kidney, potassium and blood-pressure risks without extra benefit.",
     S("ramipril", "Ramipril capsules label, 5.7 Dual Blockade of the Renin-Angiotensin-Aldosterone System (names telmisartan)"),
     [S("telmisartan", "Micardis label, 7.4 Dual Blockade of the Renin-Angiotensin-Aldosterone System")]),
    ("Losartan", "Ramipril", "unclassified", RAS, S("losartan", "Cozaar label, 7.4 Dual Blockade of the Renin-Angiotensin System (ACE inhibitors)"),
     [S("ramipril", "Ramipril capsules label, 5.7 Dual Blockade of the Renin-Angiotensin-Aldosterone System")]),
    ("Losartan", "Enalapril", "unclassified", RAS, S("enalapril", "Vasotec label, Dual Blockade of the Renin-Angiotensin System (RAS)"),
     [S("losartan", "Cozaar label, 7.4 Dual Blockade of the Renin-Angiotensin System")]),
    ("Gliclazide", "Levofloxacin", "unclassified",
     "The levofloxacin label says blood sugar can swing too low or too high in people on diabetes tablets, so sugar should be checked more often (label example: glyburide, a sulfonylurea like gliclazide).",
     S("levofloxacin", "Levofloxacin tablets label, 7.3 Antidiabetic Agents"), []),
    ("Gliclazide", "Ciprofloxacin", "unclassified",
     "The ciprofloxacin label warns of low blood sugar, sometimes severe, with diabetes tablets such as sulfonylureas, so sugar should be monitored (gliclazide is a sulfonylurea).",
     S("ciprofloxacin", "Ciprofloxacin tablets label, 7 Drug Interactions, Table 11 (Oral antidiabetic drugs); 5.19 Blood Glucose Disturbances"), []),
    ("Domperidone", "Levofloxacin", "major",
     "The domperidone product information says it must not be taken with medicines that lengthen the heart's QT interval, and it names levofloxacin among such antibiotics.",
     S("domperidone", "Domperidone EU Article 31 referral, Annex III, product information section 4.5 (contraindicated: QTc-prolonging medicinal products, antibiotics e.g. levofloxacin) and 4.3"),
     [S("levofloxacin", "Levofloxacin label, 5.11 Prolongation of the QT Interval")]),
    ("Domperidone", "Azithromycin", "unclassified", "The domperidone product information says caution is needed with azithromycin because both can affect the heart's QT interval.",
     S("domperidone", "Domperidone EU Article 31 referral, Annex III, product information section 4.5 (caution: azithromycin and roxithromycin)"),
     [S("azithromycin", "Azithromycin label, 5.4 QT Prolongation")]),
    ("Domperidone", "Ondansetron", "unclassified", QT.format(d="ondansetron"),
     S("domperidone", "Domperidone EU Article 31 referral, Annex III, section 4.3/4.5 (contraindicated: QTc-prolonging medicinal products; ondansetron is not named)"),
     [S("ondansetron", "Ondansetron tablets label, 5.2 QT Prolongation")]),
    ("Domperidone", "Ciprofloxacin", "unclassified", QT.format(d="ciprofloxacin"),
     S("domperidone", "Domperidone EU Article 31 referral, Annex III, section 4.3/4.5 (contraindicated: QTc-prolonging medicinal products; ciprofloxacin is not named)"),
     [S("ciprofloxacin", "Ciprofloxacin tablets label, 5.12 Prolongation of the QT Interval; Table 11 (Drugs Known to Prolong QT Interval)")]),
    ("Vildagliptin", "Enalapril", "unclassified", ACE.format(d="enalapril"),
     S("galvus", "Galvus SmPC, 4.5 Interaction with other medicinal products: Combination with ACE-inhibitors; 4.8 Angioedema"), []),
    ("Vildagliptin", "Ramipril", "unclassified", ACE.format(d="ramipril"),
     S("galvus", "Galvus SmPC, 4.5 Interaction with other medicinal products: Combination with ACE-inhibitors; 4.8 Angioedema"), []),
]


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; not overwriting")
    entries = [{"pair_id": f"S{i:02d}", "drug_a": a, "drug_b": b, "proposed_severity": sev, "summary_en": sm, "source_url": src["url"], "source_section": src["section"],
                "supporting_sources": sup, "fetched": "2026-10-16", "status": "draft_unreviewed"} for i, (a, b, sev, sm, src, sup) in enumerate(ROWS, 1)]
    doc = {"note": "Drafted by Claude Code from official label / regulator pages. Pairs with NO DDInter record only. Only documented interactions; no entry ever says 'no interaction'. "
                   "Ignored by the app until status is 'reviewed' (pharmacist). Summaries are own-words paraphrases. Severity 'unclassified' = the source gives no severity.",
           "entries": entries}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(entries), "entries")


if __name__ == "__main__":
    main()
