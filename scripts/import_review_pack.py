"""Summarise a returned review-pack CSV (does not change any data).
   python scripts/import_review_pack.py docs/review_pack/returned_ta.csv --reviewer AB
Validates the verdicts and the row identity against the original pack, then writes docs/review_pack/results_<lang>.md:
counts per verdict and status, and every row that is wrong_meaning or unsafe. Refuses the whole file if any row is invalid."""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACK = REPO / "docs" / "review_pack"
VERDICTS = {"correct", "understandable_but_awkward", "wrong_meaning", "unsafe"}


def read(p) -> list[dict]:
    with Path(p).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarise(returned: list[dict], original: list[dict], reviewer: str) -> tuple[list[str], str]:
    known = {(r["document_id"], r["line_id"], r["language"]): r for r in original}
    errors, seen, counts, bad = [], set(), Counter(), []
    for n, r in enumerate(returned, start=2):
        key = (r["document_id"], r["line_id"], r["language"])
        v = (r.get("reviewer_verdict") or "").strip()
        if key not in known:
            errors.append(f"row {n}: unknown line {key}")
        elif key in seen:
            errors.append(f"row {n}: duplicate line {key}")
        elif v and v not in VERDICTS:
            errors.append(f"row {n}: verdict {v!r} is not one of {sorted(VERDICTS)}")
        elif v in ("wrong_meaning", "unsafe") and not (r.get("reviewer_comment") or "").strip():
            errors.append(f"row {n}: verdict {v} needs a comment saying what is wrong")
        elif key in known and r["shown_text"] != known[key]["shown_text"]:
            errors.append(f"row {n}: shown_text differs from the pack (do not edit that column; put corrections in reviewer_comment)")
        seen.add(key)
        if v:
            counts[(known.get(key, r)["status"], v)] += 1
            if v in ("wrong_meaning", "unsafe"):
                bad.append(r)
    missing = len(known) - len(seen)
    if missing:
        errors.append(f"{missing} rows of the original pack are missing")
    lang = original[0]["language"]
    L = [f"# Review results: {lang} (reviewer {reviewer})", "", f"Rows reviewed: {sum(counts.values())} of {len(original)}.", "", "| status | verdict | rows |", "|---|---|---|"]
    L += [f"| {s} | {v} | {n} |" for (s, v), n in sorted(counts.items())]
    L += ["", "## wrong_meaning and unsafe rows", ""] + [f"- {r['document_id']} {r['line_id']} ({r['status']}): {r['reviewer_verdict']}. {r['reviewer_comment']}" for r in bad]
    return errors, "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("returned")
    ap.add_argument("--reviewer", required=True)
    a = ap.parse_args()
    ret = read(a.returned)
    lang = ret[0]["language"] if ret else ""
    errs, md = summarise(ret, read(PACK / f"review_{lang}.csv"), a.reviewer)
    if errs:
        print("REFUSED:\n  " + "\n  ".join(errs))
        sys.exit(1)
    (PACK / f"results_{lang}.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)
