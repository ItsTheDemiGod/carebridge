"""Deterministic, rule-based generator for the CareBridge synthetic dataset (no LLM, no network).

Run from the repo root:  backend\\.venv\\Scripts\\python data\\generate_synthetic.py

Writes 60 documents (40 discharge summaries "ds_NNN", 20 prescriptions "rx_NNN"):
  data/synthetic/<id>.txt       document text (LF line endings)
  data/ground_truth/<id>.json   ExtractedDocument with exact source_span offsets
  data/manifest.json            id, type, template, difficulty, dev/test split

Offsets are recorded by the text Buf at the moment each string is appended, then checked
against the final text (and again by validate_dataset.py), so they are never typed by hand.

Ground-truth conventions: brand_name, generic_name, duration_text, original_abbreviation and
special_instructions are kept AS WRITTEN (including case). strength, dose and the numeric
frequency fields are normalised (e.g. "500 mg", "1 tablet", times_per_day=2).

=== CASE TEMPLATES FOR CLINICIAN REVIEW (medicine lists; all from data/reference/formulary.json) ===
 t2dm_htn   Type 2 diabetes + hypertension : Metformin 500 BD, Glimepiride 1 OD, Telmisartan 40 OD,
                                              Atorvastatin 10 HS
 cap        Community-acquired pneumonia   : Amoxicillin+Clavulanic acid 625 BD x5, Azithromycin 500 OD x3,
                                              Paracetamol 650 SOS, Ambroxol syrup 5 mL TDS x5
 dengue     Dengue recovery                : Paracetamol 650 SOS, Pantoprazole 40 OD x5, Ondansetron 4 SOS
 appendix   Post-appendectomy              : Cefuroxime 500 BD x5, Metronidazole 400 TDS x5,
                                              Paracetamol 650 TDS x3, Pantoprazole 40 OD x5
 uti        Urinary tract infection        : Nitrofurantoin 100 BD x5, Paracetamol 500 SOS,
                                              (optional) Domperidone 10 TDS x3
 gastro     Acute gastroenteritis          : Racecadotril 100 TDS x3, Ondansetron 4 SOS, Ciprofloxacin 500 BD x3,
                                              (optional) Pantoprazole 40 OD x5
 cardiac    Post-ACS with stent            : Aspirin 75 OD, Clopidogrel 75 OD, Atorvastatin 40 HS,
                                              Metoprolol succinate 25 OD, Ramipril 2.5 OD, Pantoprazole 40 OD
 copd       COPD exacerbation              : Prednisolone 20 OD x5, Azithromycin 500 OD x3,
                                              Budesonide+Formoterol 200/6 2 puffs BD, Tiotropium 18 mcg OD,
                                              Salbutamol 100 mcg 2 puffs SOS, Pantoprazole 40 OD x5
 fracture   Tibia fracture, nail fixation  : Paracetamol 650 QID x5, Enoxaparin 40 mg OD x10,
                                              Calcium carbonate+Vitamin D3 500 OD x30, Cholecalciferol 60000 IU weekly x56
 (Chronic medicines have no duration in discharge summaries; prescriptions give x 30 days.)
"""

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.schemas.extraction import ExtractedDocument  # noqa: E402

SEED = 20250101
DIFFS = ["clean", "abbreviated", "messy"]
FORMULARY = json.loads((ROOT / "reference" / "formulary.json").read_text(encoding="utf-8"))
BY_GENERIC = {m["generic_name"]: m for m in FORMULARY["medicines"]}


def M(generic, strength, dose, freq, meal=None, days=None, note=None, optional=False):
    assert strength in BY_GENERIC[generic]["available_strengths"], (generic, strength)
    return dict(generic=generic, strength=strength, dose=dose, freq=freq, meal=meal, days=days, note=note, optional=optional)


# fus entries: (clean sentence, short sentence, [days options]); {when} is filled in at render time.
TEMPLATES = {
    "t2dm_htn": dict(
        dx=("Type 2 diabetes mellitus with hypertension", "T2DM with HTN"),
        course="{name}, a {age}-year-old {sexw}, was admitted with high blood sugar and raised blood pressure. Blood sugar was brought under control with medicines and diet advice, and blood pressure settled. The patient is being discharged in stable condition.",
        meds=[M("Metformin", "500 mg", "1 tablet", "BD", "pc"), M("Glimepiride", "1 mg", "1 tablet", "OD", "ac"),
              M("Telmisartan", "40 mg", "1 tablet", "OD"), M("Atorvastatin", "10 mg", "1 tablet", "HS")],
        fus=[("Please review at the medicine OPD {when} with fasting and post-meal blood sugar reports.", "F/U medicine OPD {when} with FBS/PPBS reports", [7, 14])],
        diet=["Follow a diabetic diet with controlled portions of rice and sweets.", "Walk for 30 minutes daily as tolerated.", "Reduce salt in food.", "Check blood sugar at home as advised."],
        flags=["Severe giddiness, sweating or fainting.", "Very high thirst or passing large amounts of urine with vomiting.", "Chest pain or breathlessness."],
    ),
    "cap": dict(
        dx=("Community-acquired pneumonia", "CAP"),
        course="{name}, a {age}-year-old {sexw}, was admitted with fever, cough and breathlessness. A chest X-ray showed a lung infection and treatment was started with antibiotics. Fever settled and breathing improved, and extra oxygen was no longer needed at discharge.",
        meds=[M("Amoxicillin + Clavulanic acid", "625 mg", "1 tablet", "BD", "pc", 5), M("Azithromycin", "500 mg", "1 tablet", "OD", None, 3),
              M("Paracetamol", "650 mg", "1 tablet", "SOS"), M("Ambroxol", "30 mg/5 mL", "5 mL", "TDS", None, 5)],
        fus=[("Please review at the chest clinic {when} with a repeat chest X-ray.", "F/U chest clinic {when} with repeat CXR", [7, 14])],
        diet=["Drink plenty of warm fluids.", "Take rest and avoid smoke and dust.", "Do deep breathing exercises as taught.", "Eat light, nutritious food."],
        flags=["Fever that does not settle.", "Worsening breathlessness or chest pain.", "Coughing up blood."],
    ),
    "dengue": dict(
        dx=("Dengue fever, recovering", "Dengue fever (recovering)"),
        course="{name}, a {age}-year-old {sexw}, was admitted with fever and body ache. The blood platelet count fell during the illness and later recovered with fluids and rest. The patient is eating well and is being discharged in stable condition.",
        meds=[M("Paracetamol", "650 mg", "1 tablet", "SOS"), M("Pantoprazole", "40 mg", "1 tablet", "OD", "ac", 5),
              M("Ondansetron", "4 mg", "1 tablet", "SOS")],
        fus=[("Please review at the medicine OPD {when} with a repeat blood count.", "F/U medicine OPD {when} with repeat CBC", [3, 5, 7])],
        diet=["Drink plenty of fluids such as ORS, coconut water and soups.", "Take adequate rest for one week.", "Avoid ibuprofen and diclofenac unless your doctor advises."],
        flags=["Bleeding from gums or nose.", "Black stools or vomiting blood.", "Severe abdominal pain or repeated vomiting.", "Extreme drowsiness or restlessness."],
    ),
    "appendix": dict(
        dx=("Acute appendicitis, post appendectomy", "Post-op appendectomy"),
        course="{name}, a {age}-year-old {sexw}, was admitted with pain in the right lower abdomen. Appendicitis was confirmed and an appendectomy was done. Recovery after surgery was uneventful and the patient is taking a normal diet.",
        meds=[M("Cefuroxime", "500 mg", "1 tablet", "BD", "pc", 5), M("Metronidazole", "400 mg", "1 tablet", "TDS", "pc", 5),
              M("Paracetamol", "650 mg", "1 tablet", "TDS", "pc", 3), M("Pantoprazole", "40 mg", "1 tablet", "OD", "ac", 5)],
        fus=[("Please review at the surgery OPD {when} for wound check.", "F/U surgery OPD {when} for wound check", [7, 10])],
        diet=["Eat light, home-cooked food and increase fibre.", "Avoid lifting heavy weights for 4 weeks.", "Keep the wound clean and dry."],
        flags=["Fever or chills.", "Redness, swelling or discharge from the wound.", "Severe abdominal pain or repeated vomiting."],
    ),
    "uti": dict(
        dx=("Urinary tract infection", "UTI"),
        course="{name}, a {age}-year-old {sexw}, was admitted with burning while passing urine and fever. Urine tests showed an infection and treatment was started. Symptoms improved and the patient is being discharged on oral medicines.",
        meds=[M("Nitrofurantoin", "100 mg", "1 capsule", "BD", "pc", 5), M("Paracetamol", "500 mg", "1 tablet", "SOS"),
              M("Domperidone", "10 mg", "1 tablet", "TDS", "ac", 3, optional=True)],
        fus=[("Please review at the medicine OPD {when} with a repeat urine test.", "F/U medicine OPD {when} with urine R/M", [5, 7])],
        diet=["Drink plenty of water.", "Do not hold urine for long periods.", "Maintain genital hygiene."],
        flags=["Fever with chills or back pain.", "Blood in urine.", "Unable to pass urine."],
    ),
    "gastro": dict(
        dx=("Acute gastroenteritis", "AGE"),
        course="{name}, a {age}-year-old {sexw}, was admitted with loose stools, vomiting and dehydration. Fluids were given through a drip and symptoms improved. The patient is now taking oral fluids and food.",
        meds=[M("Racecadotril", "100 mg", "1 capsule", "TDS", "ac", 3), M("Ondansetron", "4 mg", "1 tablet", "SOS"),
              M("Ciprofloxacin", "500 mg", "1 tablet", "BD", "pc", 3), M("Pantoprazole", "40 mg", "1 tablet", "OD", "ac", 5, optional=True)],
        fus=[("Please review at the medicine OPD {when} with a stool test if loose stools continue.", "F/U medicine OPD {when} with stool R/M if loose stools continue", [3, 5])],
        diet=["Drink ORS after each loose stool.", "Eat light food such as rice, banana and curd.", "Wash hands before eating and after using the toilet.", "Drink only boiled or filtered water."],
        flags=["Vomiting that does not stop.", "Blood in stool.", "Very little urine, dry mouth or extreme drowsiness."],
    ),
    "cardiac": dict(
        dx=("Acute coronary syndrome treated with angioplasty and stent", "ACS s/p PTCA with stent"),
        course="{name}, a {age}-year-old {sexw}, was admitted with chest pain. ECG and blood tests were done, and an angiogram showed a blocked artery. A stent was placed and the patient remained stable and pain-free afterwards.",
        meds=[M("Aspirin", "75 mg", "1 tablet", "OD", "pc"),
              M("Clopidogrel", "75 mg", "1 tablet", "OD", None, note=("Do not stop without asking your cardiologist.", "do not stop w/o asking cardiologist")),
              M("Atorvastatin", "40 mg", "1 tablet", "HS"), M("Metoprolol succinate", "25 mg", "1 tablet", "OD"),
              M("Ramipril", "2.5 mg", "1 tablet", "OD"), M("Pantoprazole", "40 mg", "1 tablet", "OD", "ac")],
        fus=[("Please review at the cardiology OPD {when} with a repeat ECG.", "F/U cardiology OPD {when} with ECG", [7, 14]),
             ("Please get a lipid profile and liver function test done {when}.", "Lipid profile and LFT {when}", [28, 30])],
        diet=["Eat a low-salt, low-fat diet.", "Walk short distances on level ground and increase slowly.", "Do not smoke.", "Avoid strenuous exercise until reviewed."],
        flags=["Chest pain not relieved by rest.", "Breathlessness or cold sweats.", "Fainting.", "Black stools or unusual bleeding."],
    ),
    "copd": dict(
        dx=("Acute exacerbation of COPD", "AECOPD"),
        course="{name}, a {age}-year-old {sexw}, was admitted with worsening breathlessness and cough. Nebulisation, steroids and antibiotics were given and breathing improved. Oxygen levels were stable at rest on the day of discharge.",
        meds=[M("Prednisolone", "20 mg", "1 tablet", "OD", "pc", 5), M("Azithromycin", "500 mg", "1 tablet", "OD", None, 3),
              M("Budesonide + Formoterol", "200/6 mcg", "2 puffs", "BD", note=("Rinse mouth after use.", "rinse mouth after use")),
              M("Tiotropium", "18 mcg", "1 capsule", "OD", note=("Inhale using the device provided.", "inhale via device")),
              M("Salbutamol", "100 mcg", "2 puffs", "SOS"), M("Pantoprazole", "40 mg", "1 tablet", "OD", "ac", 5)],
        fus=[("Please review at the chest clinic {when} with a repeat breathing test.", "F/U chest clinic {when} with PFT", [7, 14])],
        diet=["Avoid smoke, dust and strong smells.", "Practise breathing exercises as taught.", "Eat small, frequent meals."],
        flags=["Worsening breathlessness.", "Lips or fingers turning bluish.", "Fever with yellow-green sputum."],
    ),
    "fracture": dict(
        dx=("Fracture of the right tibia, post nail fixation", "# R tibia s/p IM nailing"),
        course="{name}, a {age}-year-old {sexw}, was admitted after a fall with a fracture of the right leg bone. Surgery was done to fix the bone with a nail. The wound is clean and the patient is being discharged for follow-up and walking practice.",
        meds=[M("Paracetamol", "650 mg", "1 tablet", "QID", "pc", 5),
              M("Enoxaparin", "40 mg", "1 injection", "OD", None, 10, note=("Given under the skin.", "SC")),
              M("Calcium carbonate + Vitamin D3", "500 mg", "1 tablet", "OD", "pc", 30),
              M("Cholecalciferol", "60000 IU", "1 capsule", "WK", None, 56)],
        fus=[("Please review at the orthopaedic OPD {when} with an X-ray and wound check.", "F/U ortho OPD {when} with X-ray and wound check", [10, 14])],
        diet=["Eat protein-rich and calcium-rich food.", "Keep the leg raised when resting.", "Walk only with the walker or crutches as taught."],
        flags=["Severe pain not relieved by medicines.", "Numbness, coldness or bluish colour of the toes.", "Pus or foul smell from the wound.", "Swelling or pain in the calf."],
    ),
}
RX_TEMPLATES = ["t2dm_htn", "cap", "uti", "gastro", "copd", "dengue", "cardiac"]

FIRST = ["Asha", "Ravi", "Meena", "Kumar", "Lakshmi", "Arjun", "Fatima", "Suresh", "Anitha", "Imran", "Deepa", "Vikram"]  # legacy list, only keeps the main RNG stream unchanged
FIRST_M = ["Ravi", "Kumar", "Arjun", "Suresh", "Imran", "Vikram", "Karthik", "Rahul", "Farhan", "Manoj"]
FIRST_F = ["Asha", "Meena", "Lakshmi", "Fatima", "Anitha", "Deepa", "Priya", "Kavya", "Nasreen", "Sunita"]
LAST = ["Sample", "Example", "Testwala", "Demo", "Mockerjee", "Fictional"]
DOCS = ["Dr. Anil Sample", "Dr. Priya Example", "Dr. R. Demo", "Dr. S. Testwala"]
CLUTTER = ["Page 1 of 2", "-------------------------", "Printed on: 08/03/2025 14:22", "Bill No. SYN-00231", "Ward: 3B / Bed 12",
           "Ref: SYN/DS/2025", "** continued overleaf **", "Dispensed by: ________", "Pharmacy copy", "Phone: 000-000-0000"]

PREFIX = {"tablet": ["Tab", "Tab.", "T."], "capsule": ["Cap", "Cap.", "C."], "syrup": ["Syp", "Syp.", "Syrup"],
          "injection": ["Inj", "Inj."], "ointment": ["Oint", "Oint."], "inhaler": ["Inh", "Inhaler", "Inh."]}
CLEAN_PREFIX = {"tablet": "Tab", "capsule": "Cap", "syrup": "Syrup", "injection": "Inj", "ointment": "Ointment", "inhaler": "Inhaler"}
FREQ_WORDS = {"OD": "once daily", "BD": "twice daily", "TDS": "three times daily", "QID": "four times daily",
              "HS": "at bedtime", "SOS": "only if needed", "WK": "once weekly"}
FREQ_TIMES = {"OD": 1, "BD": 2, "TDS": 3, "QID": 4, "HS": 1, "SOS": None, "WK": None}
PATTERN = {"OD": "1-0-0", "BD": "1-0-1", "TDS": "1-1-1"}
STYLE_P = {"clean": (0.1, 0.5), "abbreviated": (0.5, 0.3), "messy": (0.5, 0.25)}  # (brand-only, generic-only); rest = both

SECTIONS = {
    "clean": dict(dx="Diagnosis:", course="Hospital course:", meds="Discharge medications:", fu="Follow-up:", adv="Diet and activity advice:", flags="Warning signs - return to the hospital if you have:"),
    "abbreviated": dict(dx="Dx:", course="Course:", meds="Rx on discharge:", fu="F/U:", adv="Advice:", flags="Return if:"),
}
MESSY_HEADS = dict(dx=["DX -", "dx:", "DIAGNOSIS"], course=["COURSE IN HOSPITAL -", "h/o & course:", "Course"], meds=["TREATMENT ON DISCHARGE", "Rx -", "Meds on d/c:"],
                   fu=["review:", "F/U -", "FOLLOW UP"], adv=["adv:", "ADVICE -", "Diet / activity"], flags=["come back to hosp if:", "RETURN IF -", "Warning signs:"])


class Buf:
    """Text builder that records exact offsets of every appended string."""

    def __init__(self):
        self.parts, self.n = [], 0

    def add(self, s):
        start = self.n
        self.parts.append(s)
        self.n += len(s)
        return start

    def span(self, s):
        start = self.add(s)
        return {"start": start, "end": start + len(s), "text": s}

    def text(self):
        return "".join(self.parts)


def fmt_date(rng, diff, d=None):
    d = d or date(2025, 1, 1) + timedelta(days=rng.randrange(0, 300))
    return d.strftime(rng.choice(["%d %b %Y", "%d/%m/%y", "%d-%m-%Y"]) if diff == "messy" else "%d %b %Y")


def case_fn(rng, diff):
    r = rng.random()
    if diff == "clean":
        return lambda s: s
    if diff == "abbreviated":
        return str.upper if r < 0.25 else (lambda s: s)
    return str.upper if r < 0.3 else str.lower if r < 0.55 else (lambda s: s)


def dur_phrase(rng, diff, d):
    if d % 7 == 0 and d >= 14:
        w = d // 7
        opts = {"clean": [f"for {w} weeks"], "abbreviated": [f"x {w} weeks"], "messy": [f"x {w} weeks", f"x{w}/52", f"{w} wks"]}[diff]
    else:
        opts = {"clean": [f"for {d} days"],
                "abbreviated": [f"x {d} days", f"x {d}d"] + ([f"x {d}/7"] if d <= 14 else []),
                "messy": [f"x {d} days", f"x{d}d", f"{d} days", f"for {d}d"] + ([f"x {d}/7", f"x{d}/7"] if d <= 14 else [])}[diff]
    return rng.choice(opts)


def render_med(rng, tm, diff, is_rx):
    """Return (entry_text, medication_dict_without_span)."""
    f = BY_GENERIC[tm["generic"]]
    cs = case_fn(rng, diff)
    pb, pg = STYLE_P[diff]
    r = rng.random()
    style = "brand" if r < pb else "generic" if r < pb + pg else "both"
    brand, generic = cs(rng.choice(f["brand_names"])), cs(f["generic_name"])
    if style == "brand":
        name, bn, gn = brand, brand, None
    elif style == "generic":
        name, bn, gn = generic, None, generic
    else:
        name = f"{brand} ({generic})" if rng.random() < 0.5 else f"{generic} ({brand})"
        bn, gn = brand, generic
    prefix = CLEAN_PREFIX[f["form"]] if diff == "clean" else rng.choice(PREFIX[f["form"]])
    prefix = cs(prefix)

    strength = tm["strength"]
    shown_strength = strength
    if diff != "clean" and "/" not in strength and rng.random() < 0.5:
        shown_strength = strength.replace(" ", "", 1)
    if diff == "messy" and rng.random() < 0.10:
        shown_strength, strength = None, None
    shown_strength = cs(shown_strength) if shown_strength else None

    # frequency
    code, meal = tm["freq"], tm["meal"]
    if diff == "messy" and rng.random() < 0.3:
        meal = None
    abbr, pattern = None, False
    if diff == "clean":
        ftok = FREQ_WORDS[code]
    elif code in PATTERN and f["form"] in ("tablet", "capsule") and tm["dose"].startswith("1 ") and rng.random() < 0.3:
        ftok = abbr = PATTERN[code]
        pattern = True
    elif code == "WK":
        ftok = "once weekly"
    else:
        ftok = abbr = cs(code)
    if code == "SOS":
        label = "as_needed"
    elif code == "HS":
        label = "bedtime"
    elif meal:
        label = "before_meals" if meal == "ac" else "after_meals"
    elif pattern and ftok == "1-0-0":
        label = "morning"
    else:
        label = "unspecified"  # frequency stated, but no time of day or meal relation
    meal_s = None
    if meal:
        meal_s = {"ac": "before meals", "pc": "after meals"}[meal] if diff == "clean" else cs({"ac": "AC", "pc": "PC"}[meal])

    # dose
    dose_n = tm["dose"]
    dose_s = None if pattern else dose_n
    if dose_s and diff != "clean":
        dose_s = dose_s.replace("tablet", "tab").replace("capsule", "cap")
    # duration
    days = tm["days"] if tm["days"] is not None else (30 if is_rx else None)
    if days is not None and diff != "clean" and rng.random() < {"abbreviated": 0.25, "messy": 0.4}[diff]:
        days = None
    dur_s = cs(dur_phrase(rng, diff, days)) if days is not None else None
    # note
    note = tm["note"]
    note_s = None
    if note:
        note_s = cs(note[0] if diff == "clean" else note[1])

    head = [prefix, name, shown_strength]
    tail = [dose_s, ftok, meal_s, dur_s]
    if diff == "clean":
        entry = " ".join(x for x in head if x)
        entry += " - " + " ".join(x for x in tail if x)
        if note_s:
            entry += ". " + note_s
    else:
        sep = rng.choice([" ", "  "]) if diff == "messy" else " "
        h, t = sep.join(x for x in head if x), sep.join(x for x in tail if x)
        entry = h + (("\n    " if diff == "messy" and rng.random() < 0.35 else sep) + t)
        if note_s:
            entry += " - " + note_s

    med = dict(
        brand_name=bn, generic_name=gn, strength=strength, form=f["form"], route=f["route"], dose=dose_n,
        frequency=dict(times_per_day=FREQ_TIMES[code], timing_label=label, original_abbreviation=abbr, is_prn=code == "SOS"),
        duration_days=days, duration_text=dur_s, special_instructions=note_s,
    )
    return entry, med


def when_phrase(rng, diff, d):
    wk = d % 7 == 0
    if diff == "clean":
        return f"after {d // 7} week{'s' if d // 7 > 1 else ''}" if wk and rng.random() < 0.5 else f"after {d} days"
    if diff == "abbreviated":
        return f"in {d // 7} wk" if wk and rng.random() < 0.5 else f"in {d} days"
    return f"{d // 7}/52" if wk and rng.random() < 0.5 else f"{d}/7"


def bullet(rng, diff):
    return "- " if diff == "clean" else rng.choice(["- ", "* ", "o ", ""]) if diff == "messy" else "- "


def build(spec):
    rng = random.Random(f"{SEED}-{spec['id']}")
    diff, is_rx, tpl = spec["difficulty"], spec["document_type"] == "prescription", TEMPLATES[spec["template"]]
    b = Buf()
    rng.choice(FIRST), rng.choice(LAST)  # burn the draws the old name code made, so all other output stays identical
    age, sex = rng.randrange(24, 82), rng.choice("MF")
    nrng = random.Random(f"{SEED}-names-{spec['id']}")  # independent stream for names
    name = f"{nrng.choice(FIRST_M if sex == 'M' else FIRST_F)} {nrng.choice(LAST)}"
    sexw = "man" if sex == "M" else "woman"
    doc = rng.choice(DOCS)
    secs = SECTIONS[diff] if diff != "messy" else {k: rng.choice(v) for k, v in MESSY_HEADS.items()}
    clutter = rng.sample(CLUTTER, rng.randrange(2, 5)) if diff == "messy" else []

    def maybe_clutter():
        if clutter and rng.random() < 0.6:
            b.add(clutter.pop() + "\n")
            if rng.random() < 0.4:
                b.add("\n")

    # header
    ident = f"SYN-{'OP' if is_rx else 'IP'}-{rng.randrange(1, 9999):05d}"
    if is_rx:
        b.add("SAMPLE CITY HOSPITAL - OUTPATIENT CLINIC\n" if diff != "messy" else "Sample City Hospital  OPD\n")
        b.add(f"{doc} (Reg. No. SYN-{rng.randrange(1, 99999):05d})\n")
        b.add(f"Date: {fmt_date(rng, diff)}\n")
    else:
        b.add("SAMPLE CITY HOSPITAL\n" + ("DISCHARGE SUMMARY\n" if diff != "messy" else "Discharge summary (fictional)\n"))
    b.add(f"Patient: {name}   Age/Sex: {age}/{sex}   ID: {ident}\n")
    if not is_rx:
        adm = date(2025, 1, 1) + timedelta(days=rng.randrange(0, 300))
        b.add(f"Admitted: {fmt_date(rng, diff, adm)}   Discharged: {fmt_date(rng, diff, adm + timedelta(days=rng.randrange(2, 9)))}\n")
        b.add(f"Consultant: {doc}\n")
    b.add("\n")
    maybe_clutter()

    b.add(f"{secs['dx']} {tpl['dx'][0] if diff == 'clean' else tpl['dx'][1]}\n\n")
    if not is_rx:
        b.add(f"{secs['course']}\n" + tpl["course"].format(name=name, age=age, sexw=sexw) + "\n\n")
        maybe_clutter()

    # medications
    chosen = [m for m in tpl["meds"] if not m["optional"] or rng.random() < 0.5]
    b.add(("Rx\n" if is_rx else f"{secs['meds']}\n"))
    meds = []
    for i, tm in enumerate(chosen, 1):
        entry, med = render_med(rng, tm, diff, is_rx)
        num = {"clean": f"{i}. ", "abbreviated": f"{i}) "}.get(diff) or rng.choice([f"{i}. ", f"{i}) ", "- ", "", f"({i}) "])
        b.add(num)
        med["source_span"] = b.span(entry)
        meds.append(med)
        b.add("\n")
    b.add("\n")
    maybe_clutter()

    # follow-up
    fus = []
    fu_list = tpl["fus"][:1] if is_rx else tpl["fus"]
    if not (is_rx and diff == "messy" and rng.random() < 0.3):
        b.add(f"{secs['fu']}\n")
        for clean_s, short_s, days_opts in fu_list:
            d = rng.choice(days_opts)
            when = when_phrase(rng, diff, d)
            line = (clean_s if diff == "clean" else short_s if diff == "abbreviated" else short_s.lower()).format(when=when)
            b.add(bullet(rng, diff))
            fus.append(dict(description=line, date_text=when, days_from_discharge=d, source_span=b.span(line)))
            b.add("\n")
        b.add("\n")

    # advice
    diet = tpl["diet"][:2] if is_rx else tpl["diet"]
    b.add(f"{secs['adv']}\n")
    for a in diet:
        b.add(bullet(rng, diff) + a + "\n")
    b.add("\n")
    maybe_clutter()

    # warning signs
    flags = []
    flag_src = [] if (is_rx and rng.random() < 0.5) else (tpl["flags"][:2] if is_rx else tpl["flags"])
    if flag_src:
        b.add(f"{secs['flags']}\n")
        for fl in flag_src:
            b.add(bullet(rng, diff))
            flags.append(dict(text=fl, source_span=b.span(fl)))
            b.add("\n")
        b.add("\n")
    b.add("Sample document for software testing only. All details are fictional.\n")

    truth = dict(document_type=spec["document_type"], medications=meds, follow_ups=fus, red_flags=flags,
                 diet_activity_advice=diet, document_language="en")
    text = b.text()
    for s in [m["source_span"] for m in meds] + [x["source_span"] for x in fus + flags]:
        assert text[s["start"]:s["end"]] == s["text"], spec["id"]
    return text, ExtractedDocument.model_validate(truth)


def make_specs():
    specs = []
    tn = list(TEMPLATES)
    for i in range(40):
        specs.append(dict(id=f"ds_{i + 1:03d}", document_type="discharge_summary", template=tn[i % 9], difficulty=DIFFS[i % 3]))
    for i in range(20):
        specs.append(dict(id=f"rx_{i + 1:03d}", document_type="prescription", template=RX_TEMPLATES[i % 7], difficulty=DIFFS[i % 3]))
    rng = random.Random(SEED)
    while True:  # reshuffle until both splits cover every difficulty and doc type, and test covers every template
        rng.shuffle(specs)
        dev, test = specs[:20], specs[20:]
        if (all({s["difficulty"] for s in part} == set(DIFFS) and {s["document_type"] for s in part} == {"discharge_summary", "prescription"} for part in (dev, test))
                and {s["template"] for s in test} == set(TEMPLATES)):
            break
    for s in specs:
        s["split"] = "dev" if s in dev else "test"
    return sorted(specs, key=lambda s: s["id"])


def main():
    syn, gt = ROOT / "synthetic", ROOT / "ground_truth"
    for d in (syn, gt):
        for old in list(d.glob("*.txt")) + list(d.glob("*.json")):
            old.unlink()
    specs = make_specs()
    for spec in specs:
        text, truth = build(spec)
        (syn / f"{spec['id']}.txt").write_text(text, encoding="utf-8", newline="\n")
        (gt / f"{spec['id']}.json").write_text(truth.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = dict(seed=SEED, note="Use ONLY the dev split for prompt tuning and debugging. The test split is held out.", documents=specs)
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(specs)} documents")


if __name__ == "__main__":
    main()
