"""Phase 6d: adds the ui.* template ids for the sample (demo) mode and the "How we tested it" page (scripts/p6d_*.py, each defines STRINGS)
to data/templates/templates.json (idempotent), re-applies the four corrected photo alt texts (CORRECTED_PHOTOS; owner-approved exception, English
corrected in add_phase6a_templates.py, ta/hi redrafted as draft_unreviewed) and writes data/templates/review_sheet_phase6d_new.csv (UTF-8 with BOM).
Same honest-copy rules as 6c. python scripts/add_phase6d_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import add_phase6a_templates as P6A  # noqa: E402
import export_review_sheet as X  # noqa: E402

CORRECTED_PHOTOS = {f"ui.photo.{n}" for n in ("notebook", "blister", "clipboard", "stethoscope", "leaves", "phone")}
NEW: dict[str, tuple[str, str, str]] = {}
for _f in sorted(Path(__file__).parent.glob("p6d_*.py")):
    _m = __import__(_f.stem)
    assert not set(_m.STRINGS) & set(NEW), f"duplicate ids in {_f.name}"
    NEW.update(_m.STRINGS)


def main():
    data = json.loads(X.TEMPLATES.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in {**{t: P6A.NEW[t] for t in CORRECTED_PHOTOS}, **NEW}.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    X.TEMPLATES.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase6d_new.csv", only=set(NEW) | CORRECTED_PHOTOS)
    print(f"{len(NEW)} new templates, {len(CORRECTED_PHOTOS)} corrected, {n} sheet rows")


if __name__ == "__main__":
    main()
