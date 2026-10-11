"""Import a returned template review sheet into data/templates/templates.json.
   python scripts/import_review_sheet.py returned.csv --reviewer AB [--date 2026-10-20]
The whole file is refused (nothing written) if any row is invalid; every bad row is reported.
Rows with an empty reviewer_verdict (and no correction) are skipped. Verdicts: correct, understandable_but_awkward, wrong_meaning, unsafe.
A correction is required for wrong_meaning and unsafe, and every placeholder of the English template must be kept in it."""

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "data" / "templates" / "templates.json"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
VERDICTS = {"correct", "understandable_but_awkward", "wrong_meaning", "unsafe"}
LANGS = {"ta", "hi"}


def validate(rows: list[dict], strings: dict) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Returns (errors, accepted updates as (template_id, language, new_text_or_empty))."""
    errors, updates = [], []
    for n, r in enumerate(rows, start=2):  # row 1 is the header
        tid, lang = (r.get("template_id") or "").strip(), (r.get("language") or "").strip()
        verdict, fix = (r.get("reviewer_verdict") or "").strip(), (r.get("reviewer_correction") or "").strip()
        bad = lambda msg: errors.append(f"row {n} ({tid}/{lang}): {msg}")  # noqa: E731
        if tid not in strings:
            bad("unknown template_id")
            continue
        if lang not in LANGS:
            bad(f"unknown language {lang!r} (only ta and hi are reviewed)")
            continue
        if not verdict and not fix:
            continue
        if verdict not in VERDICTS:
            bad(f"reviewer_verdict {verdict!r} is not one of {sorted(VERDICTS)}")
            continue
        if (r.get("english") or "").strip() != strings[tid]["en"]["text"].strip():
            bad("english column differs from the current template (stale sheet; export again)")
            continue
        if verdict in ("wrong_meaning", "unsafe") and not fix:
            bad(f"verdict {verdict} needs a reviewer_correction")
            continue
        if fix:
            want, got = sorted(PLACEHOLDER.findall(strings[tid]["en"]["text"])), sorted(PLACEHOLDER.findall(fix))
            if want != got:
                bad(f"placeholders {got} in the correction do not match the template's {want}")
                continue
        updates.append((tid, lang, fix))
    return errors, updates


def import_sheet(sheet, reviewer: str, on: str | None = None, templates=TEMPLATES) -> tuple[list[str], int]:
    data = json.loads(Path(templates).read_text(encoding="utf-8"))
    with Path(sheet).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    errors, updates = validate(rows, data["strings"])
    if not reviewer.strip():
        errors.append("reviewer initials are required")
    if errors:
        return errors, 0
    for tid, lang, fix in updates:
        s = data["strings"][tid][lang]
        if fix:
            s["text"] = fix
        s.update(review_status="reviewed", reviewer=reviewer.strip(), reviewed_on=on or date.today().isoformat())
    Path(templates).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return [], len(updates)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--reviewer", required=True, help="reviewer initials")
    ap.add_argument("--date")
    a = ap.parse_args()
    errs, n = import_sheet(a.sheet, a.reviewer, a.date)
    if errs:
        print("REFUSED, nothing written:\n  " + "\n  ".join(errs))
        sys.exit(1)
    print(f"imported {n} reviewed strings")
