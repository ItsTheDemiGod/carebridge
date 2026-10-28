"""POST-HOC scratch: list the strict silent-miss cases of final-test-v1 (read-only; no model call)."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO))
from app.safety import interactions as I
from eval import phase4_safety as P4
r = P4.evaluate("final-test-v1", I.load_data(), split="test")
for s in r["silent"]:
    print(json.dumps(s, ensure_ascii=False))
print("down", len(r["down"]), "false", len(r["false_alarms"]))
