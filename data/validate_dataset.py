"""Validate the synthetic dataset. Run: backend\\.venv\\Scripts\\python data\\validate_dataset.py

validate() returns (errors, summary_rows); the script exits non-zero if there are errors.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.schemas.extraction import ExtractedDocument  # noqa: E402

DIFFS = {"clean", "abbreviated", "messy"}


def validate():
    errors = []
    formulary = json.loads((ROOT / "reference" / "formulary.json").read_text(encoding="utf-8"))["medicines"]
    by_generic = {m["generic_name"].casefold(): m for m in formulary}
    by_brand = {b.casefold(): m for m in formulary for b in m["brand_names"]}
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    docs = manifest["documents"]

    ids = {d["id"] for d in docs}
    if len(ids) != len(docs):
        errors.append("duplicate ids in manifest")
    for kind, folder, ext in (("text", "synthetic", ".txt"), ("ground truth", "ground_truth", ".json")):
        on_disk = {p.stem for p in (ROOT / folder).glob(f"*{ext}")}
        if on_disk != ids:
            errors.append(f"manifest vs {kind} files mismatch: {sorted(on_disk ^ ids)}")

    style_docs = {"brand_only": set(), "generic_only": set(), "both": set()}
    for d in docs:
        i = d["id"]
        try:
            text = (ROOT / "synthetic" / f"{i}.txt").read_bytes().decode("utf-8")  # raw: offsets must not depend on newline translation
            truth = ExtractedDocument.model_validate_json((ROOT / "ground_truth" / f"{i}.json").read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{i}: cannot load/parse ({e})")
            continue
        if truth.document_type.value != d["document_type"]:
            errors.append(f"{i}: document_type differs from manifest")
        spans = [("medication", m.source_span) for m in truth.medications] + \
                [("follow_up", f.source_span) for f in truth.follow_ups] + [("red_flag", r.source_span) for r in truth.red_flags]
        for what, s in spans:
            if text[s.start:s.end] != s.text:
                errors.append(f"{i}: {what} span does not match text at [{s.start}:{s.end}]")
        for m in truth.medications:
            ent = None
            for nm in (m.generic_name, m.brand_name):
                if nm and nm.casefold() not in by_generic and nm.casefold() not in by_brand:
                    errors.append(f"{i}: '{nm}' not in formulary")
            if m.generic_name:
                ent = by_generic.get(m.generic_name.casefold())
            if m.brand_name:
                b_ent = by_brand.get(m.brand_name.casefold())
                if ent and b_ent and ent is not b_ent:
                    errors.append(f"{i}: brand '{m.brand_name}' does not match generic '{m.generic_name}'")
                ent = ent or b_ent
            if not (m.brand_name or m.generic_name):
                errors.append(f"{i}: medication with no name")
            elif ent and m.strength and m.strength not in ent["available_strengths"]:
                errors.append(f"{i}: strength '{m.strength}' not available for {ent['generic_name']}")
            style = "both" if m.brand_name and m.generic_name else "brand_only" if m.brand_name else "generic_only"
            style_docs[style].add(i)

    c = Counter()
    for d in docs:
        c["total"] += 1
        c[d["document_type"]] += 1
        c[f"split:{d['split']}"] += 1
    expected = {"total": 60, "discharge_summary": 40, "prescription": 20, "split:dev": 20, "split:test": 40}
    for k, v in expected.items():
        if c[k] != v:
            errors.append(f"count {k}: expected {v}, got {c[k]}")
    for sp in ("dev", "test"):
        got = {d["difficulty"] for d in docs if d["split"] == sp}
        if got != DIFFS:
            errors.append(f"{sp} split difficulties: {sorted(got)}")
    templates = {d["template"] for d in docs}
    test_templates = {d["template"] for d in docs if d["split"] == "test"}
    if test_templates != templates:
        errors.append(f"test split missing templates: {sorted(templates - test_templates)}")
    for k in ("brand_only", "generic_only"):
        if len(style_docs[k]) < 8:
            errors.append(f"only {len(style_docs[k])} documents with {k} medications (need 8+)")
    if not style_docs["both"]:
        errors.append("no documents with brand+generic medications")

    rows = [("documents", c["total"]), ("discharge summaries", c["discharge_summary"]), ("prescriptions", c["prescription"]),
            ("dev / test", f"{c['split:dev']} / {c['split:test']}"), ("templates (total / in test)", f"{len(templates)} / {len(test_templates)}")]
    for sp in ("dev", "test"):
        cnt = Counter(d["difficulty"] for d in docs if d["split"] == sp)
        rows.append((f"{sp} by difficulty", ", ".join(f"{k}={cnt[k]}" for k in sorted(DIFFS))))
    rows += [(f"docs with {k} meds", len(v)) for k, v in style_docs.items()]
    rows.append(("errors", len(errors)))
    return errors, rows


if __name__ == "__main__":
    errs, rows = validate()
    w = max(len(r[0]) for r in rows)
    print("\n".join(f"{k:<{w}} | {v}" for k, v in rows))
    for e in errs:
        print("ERROR:", e)
    sys.exit(1 if errs else 0)
