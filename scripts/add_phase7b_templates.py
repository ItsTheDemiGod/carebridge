"""Phase 7b write-up: adds the ui.* template ids for the held-out test section of "How we tested it" (scripts/p7b_*.py, each defines S) to
data/templates/templates.json (idempotent), re-applies the two reworded Phase 6d strings (CHANGED; their ta/hi are redrafted as draft_unreviewed) and writes
data/templates/review_sheet_phase7b_new.csv (UTF-8 with BOM). python scripts/add_phase7b_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import export_review_sheet as X  # noqa: E402
import p6d_testing as P6D  # noqa: E402

CHANGED = {"ui.testing.method.test", "ui.testing.limits.l2"}
NEW: dict[str, tuple[str, str, str]] = {}
for _f in sorted(Path(__file__).parent.glob("p7b_*.py")):
    _m = __import__(_f.stem)
    assert not set(_m.S) & set(NEW), f"duplicate ids in {_f.name}"
    NEW.update(_m.S)
assert not set(NEW) & set(P6D.S), "a Phase 7b id collides with a Phase 6d id"


def main():
    data = json.loads(X.TEMPLATES.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in {**{t: P6D.S[t] for t in CHANGED}, **NEW}.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    X.TEMPLATES.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase7b_new.csv", only=set(NEW) | CHANGED)
    print(f"{len(NEW)} new templates, {len(CHANGED)} reworded, {n} sheet rows")


if __name__ == "__main__":
    main()
