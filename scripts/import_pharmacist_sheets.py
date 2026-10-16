"""Imports a returned pharmacist sheet (kind detected from the header). The WHOLE file is refused if any row is invalid (rows listed).
  supplement sheet: sets status "reviewed" (needs_more_info stays draft_unreviewed) in data/reference/interactions_supplement.json
  formulary sheet : stores verdicts in data/reference/formulary_review.json (formulary.json itself is never edited by this script)
Run: python scripts/import_pharmacist_sheets.py FILE.csv [--dry-run]"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"
SEVERITIES = {"major", "moderate", "minor", "unknown"}
SUP_VERDICTS = {"agree", "change_severity", "remove", "needs_more_info"}
FORM_VERDICTS = {"agree", "correct", "remove"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SheetError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def _rows(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _common(r: dict, verdicts: set[str], n: int, out: list[str]):
    v = r.get("reviewer_verdict", "")
    if v not in verdicts:
        out.append(f"row {n}: reviewer_verdict '{v}' must be one of {sorted(verdicts)}")
    if not r.get("reviewer_initials"):
        out.append(f"row {n}: reviewer_initials required")
    if not DATE.match(r.get("review_date", "")):
        out.append(f"row {n}: review_date must be YYYY-MM-DD")


def _import_supplement(rows: list[dict], ref: Path, dry_run: bool) -> str:
    sup_path = ref / "interactions_supplement.json"
    doc = json.loads(sup_path.read_text(encoding="utf-8"))
    by_id = {e["pair_id"]: e for e in doc["entries"]}
    problems: list[str] = []
    seen = set()
    for n, r in enumerate(rows, 2):
        e = by_id.get(r["pair_id"])
        if e is None:
            problems.append(f"row {n}: unknown pair_id '{r['pair_id']}'")
            continue
        if (r["drug_a"], r["drug_b"]) != (e["drug_a"], e["drug_b"]):
            problems.append(f"row {n}: drugs do not match pair_id {r['pair_id']}")
        if r["pair_id"] in seen:
            problems.append(f"row {n}: duplicate pair_id {r['pair_id']}")
        seen.add(r["pair_id"])
        _common(r, SUP_VERDICTS, n, problems)
        sev = r.get("reviewer_severity", "")
        if sev and sev not in SEVERITIES:
            problems.append(f"row {n}: reviewer_severity '{sev}' must be one of {sorted(SEVERITIES)}")
        if r.get("reviewer_verdict") == "change_severity" and sev not in SEVERITIES:
            problems.append(f"row {n}: change_severity needs a reviewer_severity")
        if r.get("reviewer_verdict") == "agree" and e["proposed_severity"] not in SEVERITIES and sev not in SEVERITIES:
            problems.append(f"row {n}: proposed severity is '{e['proposed_severity']}'; give a reviewer_severity")
    if set(by_id) - seen:
        problems.append(f"missing rows for {sorted(set(by_id) - seen)}")
    if problems:
        raise SheetError(problems)
    for r in rows:
        e = by_id[r["pair_id"]]
        e.update(reviewer_verdict=r["reviewer_verdict"], reviewer_severity=r["reviewer_severity"], reviewer_comment=r["reviewer_comment"],
                 reviewer_initials=r["reviewer_initials"], review_date=r["review_date"])
        e["status"] = "draft_unreviewed" if r["reviewer_verdict"] == "needs_more_info" else "reviewed"
    if not dry_run:
        sup_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return f"supplement: {sum(e['status'] == 'reviewed' for e in doc['entries'])} of {len(doc['entries'])} entries now reviewed"


def _import_formulary(rows: list[dict], ref: Path, dry_run: bool) -> str:
    names = {m["generic_name"] for m in json.loads((ref / "formulary.json").read_text(encoding="utf-8"))["medicines"]}
    problems: list[str] = []
    seen = set()
    for n, r in enumerate(rows, 2):
        if r["generic_name"] not in names:
            problems.append(f"row {n}: unknown generic '{r['generic_name']}'")
        if r["generic_name"] in seen:
            problems.append(f"row {n}: duplicate generic '{r['generic_name']}'")
        seen.add(r["generic_name"])
        _common(r, FORM_VERDICTS, n, problems)
        if r.get("reviewer_verdict") == "correct" and not r.get("reviewer_correction"):
            problems.append(f"row {n}: verdict 'correct' needs reviewer_correction")
    if names - seen:
        problems.append(f"missing rows for {sorted(names - seen)}")
    if problems:
        raise SheetError(problems)
    out = {r["generic_name"]: {k: r[k] for k in ("reviewer_verdict", "reviewer_correction", "reviewer_comment", "reviewer_initials", "review_date")} for r in rows}
    if not dry_run:
        (ref / "formulary_review.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return f"formulary: {len(out)} verdicts stored in formulary_review.json (apply 'correct' rows to formulary.json by hand)"


def import_sheet(path: Path, ref: Path = REF, dry_run: bool = False) -> str:
    rows = _rows(path)
    if not rows:
        raise SheetError(["empty file"])
    if "pair_id" in rows[0]:
        return _import_supplement(rows, ref, dry_run)
    if "generic_name" in rows[0]:
        return _import_formulary(rows, ref, dry_run)
    raise SheetError(["unrecognised sheet: header has neither pair_id nor generic_name"])


if __name__ == "__main__":
    try:
        print(import_sheet(Path(sys.argv[1]), dry_run="--dry-run" in sys.argv))
    except SheetError as e:
        print("REFUSED, nothing changed:\n- " + "\n- ".join(e.problems))
        sys.exit(1)
