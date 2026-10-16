"""Write data/templates/review_sheet.csv for native-speaker review of the Tamil and Hindi template strings.
UTF-8 with BOM so Excel shows Tamil and Hindi correctly.   python scripts/export_review_sheet.py"""

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "data" / "templates" / "templates.json"
SHEET = REPO / "data" / "templates" / "review_sheet.csv"
COLUMNS = ["template_id", "language", "english", "translation", "placeholders", "status", "reviewer_verdict", "reviewer_correction", "reviewer_comment"]
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def export(templates=TEMPLATES, sheet=SHEET, only=None) -> int:
    strings = json.loads(Path(templates).read_text(encoding="utf-8"))["strings"]
    rows = [[tid, lang, v["en"]["text"], v[lang]["text"], " ".join(sorted(set(PLACEHOLDER.findall(v["en"]["text"])))), v[lang]["review_status"], "", "", ""]
            for tid, v in strings.items() if only is None or tid in only for lang in ("ta", "hi")]
    with Path(sheet).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(f"wrote {export()} rows to {SHEET.relative_to(REPO)}")
