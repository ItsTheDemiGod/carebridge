"""Import a returned phrase review sheet into data/templates/phrases.json.
   python scripts/import_phrase_sheet.py returned.csv --reviewer AB [--date 2026-10-20]
Same rules as import_review_sheet.py: the whole file is refused (nothing written) if any row is invalid and every bad row is reported;
rows with no verdict and no correction are skipped. A correction must keep exactly the {placeholders} AND exactly the digits of the English
(it may not add or drop a number), must be mostly in the target script, and is required for wrong_meaning and unsafe.
Accepted rows get review_status "reviewed" plus reviewer initials and date."""

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
from app.services.script import script_ok  # noqa: E402

PHRASES = REPO / "data" / "templates" / "phrases.json"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
VERDICTS = {"correct", "understandable_but_awkward", "wrong_meaning", "unsafe"}
LANGS = {"ta", "hi"}


def digits(s: str) -> list[str]:
    return sorted(re.findall(r"[0-9]+", s))


def validate(rows: list[dict], phrases: dict[str, dict]) -> tuple[list[str], list[tuple[str, str, str]]]:
    """(errors, accepted updates as (phrase_id, language, new_text_or_empty))."""
    errors, updates = [], []
    for n, r in enumerate(rows, start=2):  # row 1 is the header
        pid, lang = (r.get("phrase_id") or "").strip(), (r.get("language") or "").strip()
        verdict, fix = (r.get("reviewer_verdict") or "").strip(), (r.get("reviewer_correction") or "").strip()
        bad = lambda msg: errors.append(f"row {n} ({pid}/{lang}): {msg}")  # noqa: E731
        if pid not in phrases:
            bad("unknown phrase_id")
            continue
        if lang not in LANGS:
            bad(f"unknown language {lang!r} (only ta and hi are reviewed)")
            continue
        if not verdict and not fix:
            continue
        en = phrases[pid]["english"]
        if verdict not in VERDICTS:
            bad(f"reviewer_verdict {verdict!r} is not one of {sorted(VERDICTS)}")
            continue
        if (r.get("english") or "").strip() != en.strip():
            bad("english column differs from the current phrase (stale sheet; export again)")
            continue
        if verdict in ("wrong_meaning", "unsafe") and not fix:
            bad(f"verdict {verdict} needs a reviewer_correction")
            continue
        if fix:
            if any(unicodedata.category(c) == "Nd" and not c.isascii() for c in fix):
                bad("use the digits 0 to 9, not native-script numerals")
                continue
            want, got = sorted(PLACEHOLDER.findall(en)), sorted(PLACEHOLDER.findall(fix))
            if want != got:
                bad(f"placeholders {got} in the correction do not match the phrase's {want}")
                continue
            if digits(fix) != digits(en):
                bad(f"numbers {digits(fix)} in the correction do not match the English {digits(en)} (a correction may not add or drop a number)")
                continue
            if not script_ok(fix.replace("{n}", "1"), lang):
                bad(f"the correction is not mostly {lang} script")
                continue
        updates.append((pid, lang, fix))
    return errors, updates


def import_sheet(sheet, reviewer: str, on: str | None = None, phrases=PHRASES) -> tuple[list[str], int]:
    data = json.loads(Path(phrases).read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in data["phrases"]}
    with Path(sheet).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    errors, updates = validate(rows, by_id)
    if not reviewer.strip():
        errors.append("reviewer initials are required")
    if errors:
        return errors, 0
    for pid, lang, fix in updates:
        s = by_id[pid][lang]
        if fix:
            s["text"] = fix
        s.update(review_status="reviewed", reviewer=reviewer.strip(), reviewed_on=on or date.today().isoformat())
    Path(phrases).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
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
    print(f"imported {n} reviewed phrases")
