"""Builds data/reference/interactions_ddinter.json (gitignored; DDInter is CC BY-NC-SA 4.0) from the raw CSVs.
Keeps only pairs between components of formulary drugs. Same pair in several rows/files: highest severity wins, disagreements counted.
Run from the repo root: python scripts/build_interaction_store.py"""
import csv
import json
import sys
from datetime import date
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.safety.names import components, formulary_generics  # noqa: E402

RANK = {"unknown": 0, "minor": 1, "moderate": 2, "major": 3}
RAW = ROOT / "data" / "reference" / "ddinter" / "raw"
OUT = ROOT / "data" / "reference" / "interactions_ddinter.json"


def key(a: str, b: str) -> str:
    return "|".join(sorted((a.lower(), b.lower())))


def build(raw_dir: Path, comps: set[str]) -> dict:
    seen: dict[str, dict] = {}
    rows = 0
    for f in sorted(Path(raw_dir).glob("ddinter_downloads_code_*.csv")):
        with f.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                rows += 1
                a, b = r["Drug_A"].strip().lower(), r["Drug_B"].strip().lower()
                if a == b or a not in comps or b not in comps:
                    continue
                e = seen.setdefault(key(a, b), {"levels": [], "files": set()})
                e["levels"].append(r["Level"].strip().lower())
                e["files"].add(f.stem[-1].upper())
    pairs = {}
    for k, e in sorted(seen.items()):
        top = max(e["levels"], key=RANK.__getitem__)
        pairs[k] = {"severity": top, "files": sorted(e["files"]), "conflicts": sum(lv != top for lv in e["levels"])}
    return {"rows_read": rows, "pairs": pairs}


def main():
    comps = {c for g in formulary_generics() for c in components(g)}
    res = build(RAW, comps)
    doc = {"provenance": {"source": "DDInter (https://ddinter.scbdd.com/download/)", "license": "CC BY-NC-SA 4.0", "downloaded": "2026-10-04",
                          "built": date.today().isoformat(), "note": "partial download: ATC groups A,B,D,H,L,P,R,V only; absence of a pair is NOT informative"},
           "pairs": res["pairs"]}
    OUT.write_text(json.dumps(doc, indent=0, ensure_ascii=False), encoding="utf-8")
    p = res["pairs"]
    print(f"rows read {res['rows_read']}; formulary components {len(comps)}; pairs kept {len(p)}; "
          f"with conflicts {sum(v['conflicts'] > 0 for v in p.values())}; levels { {s: sum(v['severity'] == s for v in p.values()) for s in RANK} }")


if __name__ == "__main__":
    main()
