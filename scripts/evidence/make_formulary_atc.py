"""Writes data/reference/formulary_atc.json: ATC codes AUTHORED from general knowledge (not verified; pharmacist review required).
Each formulary entry lists its components (one for a single drug, several for a combination product) with the DDInter spelling
(from data/reference/ddinter_coverage.py RENAME) and the component's own ATC codes. Run from the repo root."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "data" / "reference"))
from ddinter_coverage import components  # noqa: E402

ATC = {
    "Metformin": ["A10BA02"], "Glimepiride": ["A10BB12"], "Gliclazide": ["A10BB09"], "Sitagliptin": ["A10BH01"], "Vildagliptin": ["A10BH02"],
    "Pioglitazone": ["A10BG03"], "Dapagliflozin": ["A10BK01"], "Empagliflozin": ["A10BK03"],
    "Amlodipine": ["C08CA01"], "Telmisartan": ["C09CA07"], "Losartan": ["C09CA01"], "Olmesartan": ["C09CA08"], "Ramipril": ["C09AA05"],
    "Enalapril": ["C09AA02"], "Metoprolol succinate": ["C07AB02"], "Atenolol": ["C07AB03"], "Bisoprolol": ["C07AB07"], "Carvedilol": ["C07AG02"],
    "Furosemide": ["C03CA01"], "Torsemide": ["C03CA04"], "Spironolactone": ["C03DA01"], "Isosorbide mononitrate": ["C01DA14"],
    "Atorvastatin": ["C10AA05"], "Rosuvastatin": ["C10AA07"],
    "Aspirin": ["B01AC06", "N02BA01"], "Clopidogrel": ["B01AC04"], "Ticagrelor": ["B01AC24"], "Enoxaparin": ["B01AB05"],
    "Pantoprazole": ["A02BC02"], "Rabeprazole": ["A02BC04"], "Omeprazole": ["A02BC01"], "Esomeprazole": ["A02BC05"], "Famotidine": ["A02BA03"],
    "Domperidone": ["A03FA03"], "Ondansetron": ["A04AA01"], "Racecadotril": ["A07XA04"], "Lactulose": ["A06AD11"],
    "Paracetamol": ["N02BE01"], "Ibuprofen": ["M01AE01"], "Diclofenac": ["M01AB05"], "Aceclofenac": ["M01AB16"],
    "Amoxicillin": ["J01CA04"], "Amoxicillin + Clavulanic acid": ["J01CR02"], "Azithromycin": ["J01FA10"], "Cefixime": ["J01DD08"],
    "Cefuroxime": ["J01DC02"], "Cefpodoxime": ["J01DD13"], "Ciprofloxacin": ["J01MA02"], "Levofloxacin": ["J01MA12"], "Nitrofurantoin": ["J01XE01"],
    "Metronidazole": ["P01AB01", "J01XD01"], "Mupirocin": ["D06AX09"],
    "Cetirizine": ["R06AE07"], "Levocetirizine": ["R06AE09"], "Montelukast": ["R03DC03"], "Salbutamol": ["R03AC02"],
    "Budesonide + Formoterol": ["R03AK07"], "Tiotropium": ["R03BB04"], "Ambroxol": ["R05CB06"],
    "Prednisolone": ["H02AB06"], "Levothyroxine": ["H03AA01"], "Calcium carbonate + Vitamin D3": ["A12AX"], "Cholecalciferol": ["A11CC05"],
    "Folic acid": ["B03BB01"], "Tamsulosin": ["G04CA02"], "Gabapentin": ["N03AX12"],
}
# component ATC for combination products (display names are the formulary's words)
COMP_ATC = {
    ("Amoxicillin + Clavulanic acid", "Amoxicillin"): ["J01CA04"], ("Amoxicillin + Clavulanic acid", "Clavulanic acid"): ["J01CR02"],
    ("Budesonide + Formoterol", "Budesonide"): ["R03BA02"], ("Budesonide + Formoterol", "Formoterol"): ["R03AC13"],
    ("Calcium carbonate + Vitamin D3", "Calcium carbonate"): ["A12AA04"], ("Calcium carbonate + Vitamin D3", "Cholecalciferol"): ["A11CC05"],
}


def main():
    meds = json.loads((ROOT / "data/reference/formulary.json").read_text(encoding="utf-8"))["medicines"]
    out = []
    for m in meds:
        g = m["generic_name"]
        dd = components(g)
        comps = []
        for d in dd:
            codes = COMP_ATC.get((g, d), ATC[g]) if len(dd) > 1 else ATC[g]
            comps.append({"ddinter_name": d, "atc_codes": codes})
        out.append({"generic_name": g, "atc_codes": ATC[g], "components": comps, "combination": len(dd) > 1})
    assert [o["generic_name"] for o in out] == [m["generic_name"] for m in meds] and len(out) == 66
    doc = {
        "status": "authored_requires_pharmacist_review",
        "source_note": "ATC codes written by Claude Code from general knowledge of the WHO ATC index; NOT checked against the WHO list. Used only to decide which drugs a DDInter file for that ATC letter can contain. A pharmacist must review (data/reference/review/formulary_atc_review.csv).",
        "downloaded_letters": list("ABDHLPRV"),
        "medicines": out,
        "review": {},
    }
    target = Path(__file__).resolve().parent / "formulary_atc.json"
    if target.exists():  # keep pharmacist verdicts already imported
        doc["review"] = json.loads(target.read_text(encoding="utf-8")).get("review", {})
    target.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", len(out))


if __name__ == "__main__":
    main()
