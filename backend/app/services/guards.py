"""Privacy and test-set guards. Gemini free tier may use submitted content for training and human review,
so only synthetic repo documents may ever be sent."""

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ALLOWED_DIRS = (REPO / "data" / "synthetic", REPO / "data" / "rendered")
TEST_LOG = REPO / "eval" / "test_runs.log"


class NotSyntheticError(PermissionError):
    pass


def assert_synthetic(path, allowed=ALLOWED_DIRS) -> Path:
    p = Path(path).resolve()
    if not any(p.is_relative_to(Path(a).resolve()) for a in allowed):
        raise NotSyntheticError(f"Refusing to send {p.name}: only files inside data/synthetic or data/rendered may be sent to Gemini")
    return p


def check_split(split: str, final_test_run: bool, what: str, log=TEST_LOG) -> None:
    """Running on the test split needs --final-test-run; every such run is logged."""
    if split == "dev":
        return
    if not final_test_run:
        raise SystemExit(f"Refusing to run '{what}' on the '{split}' split without --final-test-run (test split is never used for tuning).")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "split": split, "what": what}) + "\n")
