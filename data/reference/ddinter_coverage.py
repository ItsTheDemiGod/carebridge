"""Coverage of the 66 formulary drugs in the downloaded DDInter CSVs. Prints markdown tables (see docs/DDINTER_COVERAGE.md).
Run from the repo root after fetch_ddinter.py:  python data/reference/ddinter_coverage.py"""
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
RANK = {"Major": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}
DOWNLOADED = set("ABDHLPRV")
# ATC first letter (anatomical group) assigned from general knowledge, NOT verified against the WHO list.
ATC = dict(zip(
    [m["generic_name"] for m in json.loads((HERE / "formulary.json").read_text(encoding="utf-8"))["medicines"]],
    "A" * 8 + "C" * 16 + "B" * 4 + "A" * 9 + "N" + "M" * 3 + "J" * 9 + "PD" + "R" * 7 + "HH" + "AA" + "BGN",
))
assert len(ATC) == 66
RENAME = {"Aspirin": ["Acetylsalicylic acid"], "Paracetamol": ["Acetaminophen"], "Torsemide": ["Torasemide"], "Metoprolol succinate": ["Metoprolol"], "Calcium carbonate + Vitamin D3": ["Calcium carbonate", "Cholecalciferol"]}  # salt form, INN/USAN synonyms, D3 = cholecalciferol


def components(g):
    return RENAME.get(g) or [c.strip() for c in g.split(" + ")]


def main():
    best = {}  # frozenset of DDInter names -> strongest level
    for f in sorted((HERE / "ddinter" / "raw").glob("*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            k = frozenset((r["Drug_A"].lower(), r["Drug_B"].lower()))
            if RANK[r["Level"]] >= RANK.get(best.get(k), -1):
                best[k] = r["Level"]
    names = {n for k in best for n in k}
    drugs = list(ATC)
    found = {d: [c for c in components(d) if c.lower() in names] for d in drugs}
    full = [d for d in drugs if len(found[d]) == len(components(d))]
    missing = [d for d in drugs if not found[d]]
    out = ["| Formulary drug | ATC group (unverified) | In downloaded groups? | DDInter name(s) matched |", "|---|---|---|---|"]
    for d in drugs:
        out.append(f"| {d} | {ATC[d]} | {'yes' if ATC[d] in DOWNLOADED else 'NO'} | {', '.join(found[d]) or 'MISSING'} |")
    pairs = Counter()
    nodata, nodata_groups = [], Counter()
    for a, b in combinations(drugs, 2):
        lv = [best[frozenset((x.lower(), y.lower()))] for x in found[a] for y in found[b] if frozenset((x.lower(), y.lower())) in best]
        cls = "both in missing groups" if ATC[a] not in DOWNLOADED and ATC[b] not in DOWNLOADED else "at least one in downloaded groups"
        if lv:
            pairs[(cls, max(lv, key=RANK.get))] += 1
        elif a in missing or b in missing or cls == "both in missing groups":
            nodata.append((a, b))
            nodata_groups[cls if a not in missing and b not in missing else "a drug not in DDInter"] += 1
        else:
            pairs[(cls, "none listed")] += 1
    print(f"formulary drugs {len(drugs)}; all components found {len(full)}; partly {len(drugs) - len(full) - len(missing)}; none {len(missing)}: {missing}")
    print("missing-group drugs:", {g: [d for d in drugs if ATC[d] == g] for g in "CGJMNS"})
    print(f"total drug pairs {len(drugs) * (len(drugs) - 1) // 2}; no-data pairs {len(nodata)} {dict(nodata_groups)}")
    print("\n".join(f"{k}: {v}" for k, v in sorted(pairs.items())))
    print("\n".join(out))


if __name__ == "__main__":
    main()
