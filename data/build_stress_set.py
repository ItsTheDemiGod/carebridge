"""Safety stress set (Phase 7a): about 30 synthetic prescriptions that exercise the safety branches the 60-document set barely touches.

  backend\\.venv\\Scripts\\python data\\build_stress_set.py [--render]

Deterministic with its OWN seed (STRESS_SEED), separate from the dev/test generator. It imports formatting helpers (render_med, Buf, name lists) from
data/generate_synthetic.py but never regenerates or reads the 60-document set. Output (committed): data/stress/synthetic/st_NN.txt, data/stress/ground_truth/st_NN.json
(same ExtractedDocument schema) and data/stress/manifest.json (id, category, difficulty, number of medicines; NO interaction levels or expected statuses: those are
computed at run time from the local DDInter-derived store). --render writes gitignored images to data/stress/rendered/{clean,photo}/ and one small preview.
The drug PAIRS are chosen from the local store at build time (the choice is a list of drug names, not DDInter data); a missing store stops the build.
Every medicine is a formulary drug with ONE exception: category eye_drop_od uses timolol eye drops, which the formulary does not contain (documented)."""
import argparse
import json
import random
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO))

import generate_synthetic as G  # noqa: E402  (formatting helpers only)
from app.safety import interactions as I  # noqa: E402
from app.schemas.extraction import ExtractedDocument  # noqa: E402

STRESS_SEED = 20261018
OUT = ROOT / "stress"
CATEGORIES = ["major_pair", "moderate_pair", "supplement_pair", "duplicate", "garbled_name", "weekly", "unusual_strength", "eye_drop_od", "long_list", "control"]
PER_CATEGORY = 3
DIFFS = ["clean", "abbreviated", "clean"]  # per document of a category: readable first; one abbreviated style each


# ------------------------------------------------------------------------------------------------------------------ drugs
def oral_generics() -> list[str]:
    return sorted(g for g, m in G.BY_GENERIC.items() if m["form"] in ("tablet", "capsule") and m["route"] == "oral" and "+" not in g)


def tm(generic: str, rng: random.Random, **kw) -> dict:
    f = G.BY_GENERIC[generic]
    unit = f["form"]
    base = dict(generic=generic, strength=f["available_strengths"][0], dose=f"1 {unit}", freq=rng.choice(["OD", "BD", "BD"]), meal=rng.choice([None, "pc", "ac"]),
                days=rng.choice([5, 7, 10, 14, 30]), note=None, optional=False)
    base.update(kw)
    return base


def pairs_by_level(data, drugs: list[str]) -> dict[str, list[tuple[str, str]]]:
    out = {"major": [], "moderate": [], "minor": [], "unknown": [], "none": [], "supplement": []}
    for a, b in combinations(drugs, 2):
        r = I.check(a, b, data)
        if r.status == I.FOUND:
            out[r.level].append((a, b))
            if I.pair_key(a, b) in data.supplement and r.source != "ddinter":
                out["supplement"].append((a, b))
        else:
            out["none"].append((a, b))
    return out


def no_record_group(data, drugs, rng, size=4) -> list[str]:
    """A small group in which no pair has a record (controls)."""
    for _ in range(2000):
        g = rng.sample(drugs, size)
        if all(I.check(a, b, data).status != I.FOUND for a, b in combinations(g, 2)):
            return g
    raise SystemExit("could not find a no-record group")


def long_group(data, drugs, rng, size=8) -> list[str]:
    """Eight drugs with as many pairs with a record as a greedy pick finds (several interacting pairs)."""
    start = rng.choice([p for p in pairs_by_level(data, drugs)["moderate"]])
    g = list(start)
    while len(g) < size:
        best = max((d for d in drugs if d not in g), key=lambda d: (sum(I.check(d, x, data).status == I.FOUND for x in g), rng.random()))
        g.append(best)
    return g


def garble(name: str, rng: random.Random) -> str:
    """A near-miss of a printed name: one letter replaced or two adjacent letters swapped (the result is never an exact formulary name)."""
    for _ in range(50):
        i = rng.randrange(1, len(name) - 1)
        if rng.random() < 0.5 and name[i] != name[i + 1]:
            s = name[:i] + name[i + 1] + name[i] + name[i + 2:]
        else:
            s = name[:i] + rng.choice("aeinorstuy") + name[i + 1:]
        if s.lower() != name.lower():
            return s
    return name + "e"


def choose(data, rng: random.Random) -> dict[str, list[list[dict]]]:
    """category -> list of documents, each a list of medicine specs (render_med input). Pure given the data."""
    drugs = oral_generics()
    lv = pairs_by_level(data, drugs)
    pick = lambda pairs, n: rng.sample(sorted(pairs), min(n, len(pairs)))  # noqa: E731
    docs: dict[str, list[list[dict]]] = {c: [] for c in CATEGORIES}
    spare = lambda used: rng.sample([d for d in drugs if d not in used], 1)[0]  # noqa: E731
    for cat, key in (("major_pair", "major"), ("moderate_pair", "moderate"), ("supplement_pair", "supplement")):
        for a, b in pick(lv[key], PER_CATEGORY):
            docs[cat].append([tm(a, rng), tm(b, rng), tm(spare({a, b}), rng)])
    for k in range(PER_CATEGORY):  # the same drug twice: same name twice, brand and generic of one drug, or two brands of one generic
        g = rng.choice([d for d in drugs if len(G.BY_GENERIC[d]["brand_names"]) >= 2])
        other = spare({g})
        docs["duplicate"].append([tm(g, rng, freq="OD"), tm(other, rng), tm(g, rng, freq="BD")])
    for k in range(PER_CATEGORY):
        a, b = rng.choice(sorted(lv["moderate"] + lv["major"]))
        docs["garbled_name"].append([tm(a, rng, _garble=True), tm(b, rng), tm(spare({a, b}), rng)])
    for k in range(PER_CATEGORY):
        docs["weekly"].append([tm("Cholecalciferol", rng, freq="WK", days=56, strength="60000 IU", meal=None), tm(spare({"Cholecalciferol"}), rng), tm(spare({"Cholecalciferol"}), rng)])
    for k in range(PER_CATEGORY):
        g = rng.choice(drugs)
        odd = rng.choice(["250 mg", "75 mg", "1500 mg", "7.5 mg"])
        odd = odd if odd not in G.BY_GENERIC[g]["available_strengths"] else "125 mg"
        docs["unusual_strength"].append([tm(g, rng, strength=odd), tm(spare({g}), rng)])
    for k in range(PER_CATEGORY):
        docs["eye_drop_od"].append([dict(eye_drop=True, variant=k), tm(spare(set()), rng), tm(spare(set()), rng)])
    for k in range(PER_CATEGORY):
        docs["long_list"].append([tm(g, rng) for g in long_group(data, drugs, rng)])
    for k in range(PER_CATEGORY):
        docs["control"].append([tm(g, rng) for g in no_record_group(data, drugs, rng, rng.choice([3, 4]))])
    return docs


# --------------------------------------------------------------------------------------------------------------- document
def eye_drop(rng, variant: int, diff: str) -> tuple[str, dict]:
    forms = ["Eye Drops Timolol 0.5% - 1 drop OD", "Timolol 0.5% eye drops 1 drop OD", "Timolol 0.5% Eye Drops - 1 drop OD x 30 days"]
    entry = forms[variant % 3]
    med = dict(brand_name=None, generic_name="Timolol", strength="0.5%", form="drops", route="other", dose="1 drop",
               frequency=dict(times_per_day=1, timing_label="unspecified", original_abbreviation="OD", is_prn=False),
               duration_days=30 if "30 days" in entry else None, duration_text="x 30 days" if "30 days" in entry else None, special_instructions=None)
    return entry, med


def build_doc(doc_id: str, category: str, specs: list[dict], diff: str) -> tuple[str, ExtractedDocument]:
    rng = random.Random(f"{STRESS_SEED}-{doc_id}")
    b = G.Buf()
    nrng = random.Random(f"{STRESS_SEED}-names-{doc_id}")
    sex = rng.choice("MF")
    name = f"{nrng.choice(G.FIRST_M if sex == 'M' else G.FIRST_F)} {nrng.choice(G.LAST)}"
    b.add("SAMPLE CITY HOSPITAL - OUTPATIENT CLINIC\n")
    b.add(f"{rng.choice(G.DOCS)} (Reg. No. SYN-{rng.randrange(1, 99999):05d})\n")
    b.add(f"Date: {G.fmt_date(rng, 'clean')}\n")
    b.add(f"Patient: {name}   Age/Sex: {rng.randrange(24, 82)}/{sex}   ID: SYN-OP-{rng.randrange(1, 9999):05d}\n\n")
    b.add("Diagnosis: Follow-up visit\n\n")
    b.add("Rx\n")
    meds = []
    for i, spec in enumerate(specs, 1):
        if spec.get("eye_drop"):
            entry, med = eye_drop(rng, spec["variant"], diff)
        else:
            garble_it = spec.pop("_garble", False)
            entry, med = G.render_med(rng, spec, diff, True)
            if garble_it:  # the printed name becomes a near-miss; ground truth keeps the name as written (the document is the reference)
                target = med["brand_name"] or med["generic_name"]
                bad = garble(target, rng)
                entry = entry.replace(target, bad, 1)
                for k in ("brand_name", "generic_name"):
                    if med[k] == target:
                        med[k] = bad
        b.add({"clean": f"{i}. ", "abbreviated": f"{i}) "}[diff])
        med["source_span"] = b.span(entry)
        meds.append(med)
        b.add("\n")
    b.add("\n")
    when = f"after {rng.choice([7, 14, 30])} days"
    b.add("Follow-up:\n")
    b.add("- ")
    fu = dict(description=f"Review {when}.", date_text=when, days_from_discharge=int(when.split()[1]), source_span=b.span(f"Review {when}."))
    b.add("\n\nAdvice:\n")
    diet = ["Drink plenty of water.", "Take medicines at the same time each day."]
    for a in diet:
        b.add("- " + a + "\n")
    b.add("\nSample document for software testing only. All details are fictional.\n")
    truth = dict(document_type="prescription", medications=meds, follow_ups=[fu], red_flags=[], diet_activity_advice=diet, document_language="en")
    text = b.text()
    for s in [m["source_span"] for m in meds] + [fu["source_span"]]:
        assert text[s["start"]:s["end"]] == s["text"], doc_id
    return text, ExtractedDocument.model_validate(truth)


def build_all(data=None, out: Path = OUT) -> list[dict]:
    data = data or I.load_data()
    if data.store is None:
        raise SystemExit("the local DDInter-derived store is missing (python scripts/build_interaction_store.py): the stress set needs it to choose drug pairs")
    rng = random.Random(STRESS_SEED)
    plan = choose(data, rng)
    (out / "synthetic").mkdir(parents=True, exist_ok=True)
    (out / "ground_truth").mkdir(parents=True, exist_ok=True)
    manifest, n = [], 0
    for cat in CATEGORIES:
        for k, specs in enumerate(plan[cat]):
            n += 1
            doc_id = f"st_{n:02d}"
            diff = DIFFS[k % len(DIFFS)]
            text, gt = build_doc(doc_id, cat, [dict(s) for s in specs], diff)
            (out / "synthetic" / f"{doc_id}.txt").write_text(text, encoding="utf-8", newline="\n")
            (out / "ground_truth" / f"{doc_id}.json").write_text(gt.model_dump_json(indent=1) + "\n", encoding="utf-8", newline="\n")
            manifest.append(dict(id=doc_id, category=cat, difficulty=diff, medicines=len(gt.medications), document_type="prescription"))
    (out / "manifest.json").write_text(json.dumps(dict(seed=STRESS_SEED, note="Safety stress set: synthetic prescriptions, formulary names (eye drop category excepted), fictional patients. Interaction levels are NOT stored here; they come from the local store at run time.", documents=manifest), indent=1) + "\n", encoding="utf-8", newline="\n")
    return manifest


def render(out: Path = OUT) -> None:
    import render_documents as RD
    font = RD.load_font()
    docs = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["documents"]
    for d in docs:
        text = (out / "synthetic" / f"{d['id']}.txt").read_text(encoding="utf-8")
        for cond in ("clean", "photo"):
            img = RD.draw_page(text, font)[0] if cond == "clean" else RD.render(text, cond, d["id"], font)[0]
            (out / "rendered" / cond).mkdir(parents=True, exist_ok=True)
            img.save(out / "rendered" / cond / f"{d['id']}.png")
    from PIL import Image
    ims = [Image.open(out / "rendered" / c / f"{docs[0]['id']}.png").convert("L") for c in ("clean", "photo")]
    w = 520
    ims = [i.resize((w, int(i.height * w / i.width))) for i in ims]
    sheet = Image.new("L", (w * 2 + 30, max(i.height for i in ims) + 20), 120)
    for k, im in enumerate(ims):
        sheet.paste(im, (10 + k * (w + 10), 10))
    dest = REPO / "docs" / "samples" / "stress_preview.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    m = build_all()
    from collections import Counter
    print(f"wrote {len(m)} prescriptions:", dict(Counter(d["category"] for d in m)))
    if a.render:
        render()
        print("rendered clean and photo images (gitignored) and docs/samples/stress_preview.png")


if __name__ == "__main__":
    main()
