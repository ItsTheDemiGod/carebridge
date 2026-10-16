"""Write data/templates/phrase_review_sheet.csv (UTF-8 with BOM, for Excel) for native-speaker review of the phrase library.
   python scripts/export_phrase_sheet.py"""

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PHRASES = REPO / "data" / "templates" / "phrases.json"
SHEET = REPO / "data" / "templates" / "phrase_review_sheet.csv"
COLUMNS = ["phrase_id", "kind", "language", "english", "translation", "placeholders", "status", "reviewer_verdict", "reviewer_correction", "reviewer_comment"]


def export(phrases=PHRASES, sheet=SHEET) -> int:
    rows = [[p["id"], p["kind"], lang, p["english"], p[lang]["text"], " ".join(sorted(set(re.findall(r"\{(\w+)\}", p["english"])))), p[lang]["review_status"], "", "", ""]
            for p in json.loads(Path(phrases).read_text(encoding="utf-8"))["phrases"] for lang in ("ta", "hi")]
    with Path(sheet).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(f"wrote {export()} rows to {SHEET.relative_to(REPO)}")
