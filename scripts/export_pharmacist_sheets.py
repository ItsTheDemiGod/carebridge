"""Writes the two pharmacist review sheets (UTF-8 with BOM) into data/reference/review/.
  interactions_supplement_review.csv  safety content: drafted interaction pairs (all start draft_unreviewed)
  formulary_review.csv                brands, strengths, form, route of the formulary (the formulary file is marked unverified)
Run from the repo root: python scripts/export_pharmacist_sheets.py"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"
OUT = REF / "review"
SUP_COLS = ["pair_id", "drug_a", "drug_b", "proposed_severity", "summary_en", "source_url", "source_section", "basis", "status",
            "reviewer_verdict", "reviewer_severity", "reviewer_comment", "reviewer_initials", "review_date"]
FORM_COLS = ["generic_name", "brand_names", "strengths", "form", "route", "status",
             "reviewer_verdict", "reviewer_correction", "reviewer_comment", "reviewer_initials", "review_date"]


def write(path: Path, cols: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in cols} for r in rows)


def main(ref: Path = REF, out: Path = OUT):
    sup = json.loads((ref / "interactions_supplement.json").read_text(encoding="utf-8"))["entries"]
    also = lambda e: " | also: " + "; ".join(s["section"] for s in e["supporting_sources"]) if e["supporting_sources"] else ""  # noqa: E731
    write(out / "interactions_supplement_review.csv", SUP_COLS, [e | {"source_section": e["source_section"] + also(e)} for e in sup])
    form = json.loads((ref / "formulary.json").read_text(encoding="utf-8"))["medicines"]
    write(out / "formulary_review.csv", FORM_COLS,
          [{"generic_name": m["generic_name"], "brand_names": "; ".join(m["brand_names"]), "strengths": "; ".join(m["available_strengths"]),
            "form": m["form"], "route": m["route"], "status": "draft_unreviewed"} for m in form])
    print(f"wrote {len(sup)} supplement rows and {len(form)} formulary rows to {out}")


if __name__ == "__main__":
    main()
