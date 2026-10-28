"""Phase 8a: static copy of the consent notice (en, ta, hi) for the hosted-sample build, generated from the same templates the real API serves
(backend/app/services/consent.py), so the hosted /privacy page makes no API call. python scripts/build_static_privacy.py [--check]"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
from app.services import consent  # noqa: E402

OUT = REPO / "frontend" / "src" / "data" / "consent-notice.generated.json"


def build() -> str:
    return json.dumps({lang: consent.notice(lang) for lang in ("en", "ta", "hi")}, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = build()
    if a.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("up to date" if ok else "STALE: python scripts/build_static_privacy.py")
        sys.exit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
