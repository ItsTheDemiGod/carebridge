"""Writes frontend/src/i18n/strings.generated.json: every ui.* template per language with its review_status, plus one
sample line (ui.sample.line) copied from an existing template so the landing page can show real fixed wording offline.
python scripts/export_ui_strings.py"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "data" / "templates" / "templates.json"
OUT = REPO / "frontend" / "src" / "i18n" / "strings.generated.json"
SAMPLE_SOURCE = "schedule.notice"  # existing fixed wording, exists in en/ta/hi


def build() -> str:
    strings = json.loads(TEMPLATES.read_text(encoding="utf-8"))["strings"]
    picked = {tid: v for tid, v in strings.items() if tid.startswith("ui.")}
    picked["ui.sample.line"] = strings[SAMPLE_SOURCE]
    out = {lang: {tid: {"text": v[lang]["text"], "review_status": v[lang]["review_status"]} for tid, v in sorted(picked.items())} for lang in ("en", "ta", "hi")}
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
