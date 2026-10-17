"""Phase 6c: adds the ui.* template ids for metadata, header, icons, photos, review redesign and phone layouts to
data/templates/templates.json (idempotent) and writes data/templates/review_sheet_phase6c_new.csv (only these ids, UTF-8 with BOM).
Every ta/hi string is draft_unreviewed (machine-drafted). English follows the honest-copy rules in docs/DESIGN.md: no "safe" except the negated form,
no claim that anyone reviewed anything, no numbers. Backend-owned text (consent notice, errors, confirmation, schedule, results) is NOT duplicated here.
python scripts/add_phase6c_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import export_review_sheet as X  # noqa: E402

NEW: dict[str, tuple[str, str, str]] = {}

# per-area string modules (scripts/p6c_*.py, each defines STRINGS)
for _f in sorted(Path(__file__).parent.glob("p6c_*.py")):
    _m = __import__(_f.stem)
    assert not set(_m.STRINGS) & set(NEW), f"duplicate ids in {_f.name}"
    NEW.update(_m.STRINGS)


def main():
    p = X.TEMPLATES
    data = json.loads(p.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in NEW.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase6c_new.csv", only=set(NEW))
    print(f"{len(NEW)} templates, {n} sheet rows")


if __name__ == "__main__":
    main()
