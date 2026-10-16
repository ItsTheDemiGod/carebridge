"""Write docs/openapi.json from the app (the contract the frontend builds against). Deterministic: no timestamps, sorted keys.
python scripts/export_openapi.py          (a test fails if the committed file is out of date)"""
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "openapi.json"


def build() -> str:
    sys.path.insert(0, str(REPO / "backend"))
    from app.config import Settings
    from app.main import create_app

    cfg = Settings(_env_file=None, carebridge_data_key="x", db_path=str(Path(tempfile.gettempdir()) / "openapi-unused.db"))  # the schema does not start the app: no key is read, no database is opened
    return json.dumps(create_app(cfg).openapi(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
