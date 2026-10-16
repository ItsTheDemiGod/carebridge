"""Interaction lookup: a table lookup, no model. Exactly four statuses; a pair that is not found is NEVER reported as safe.

  interaction_found            level + source (ddinter | curated_reviewed)
  not_checked_no_record        no record in the DDInter-derived store or the REVIEWED supplement (says nothing about safety)
  not_checked_unconfirmed      one or both medicines are not interaction_ready (generic passed as None)
  not_checked_database_missing the DDInter-derived store file is absent or unreadable
The DDInter download is partial, so absence is uninformative (docs/SAFETY.md)."""
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.safety.names import components
from app.services.guards import REPO

STORE_PATH = REPO / "data" / "reference" / "interactions_ddinter.json"
SUPPLEMENT_PATH = REPO / "data" / "reference" / "interactions_supplement.json"
RANK = {"unknown": 0, "minor": 1, "moderate": 2, "major": 3}
FOUND, NO_RECORD, UNCONFIRMED, DB_MISSING = "interaction_found", "not_checked_no_record", "not_checked_unconfirmed", "not_checked_database_missing"
STATUSES = (FOUND, NO_RECORD, UNCONFIRMED, DB_MISSING)


@dataclass(frozen=True)
class Result:
    status: str
    level: str | None = None
    source: str | None = None


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a.lower(), b.lower())))


@dataclass
class Data:
    """store: component-pair key -> {severity,...} (None = file missing). supplement: formulary-generic pair key -> entry, REVIEWED entries only."""
    store: dict | None
    supplement: dict = field(default_factory=dict)
    supplement_pending: int = 0


def load_store(path: Path = STORE_PATH) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))["pairs"]
    except (OSError, ValueError, KeyError):
        return None


def load_supplement(path: Path = SUPPLEMENT_PATH) -> tuple[dict, int]:
    """(reviewed entries by pair key, number of entries ignored because they are not reviewed). A missing/broken file is an empty supplement."""
    try:
        entries = json.loads(Path(path).read_text(encoding="utf-8"))["entries"]
    except (OSError, ValueError, KeyError):
        return {}, 0
    ok = {pair_key(e["drug_a"], e["drug_b"]): e for e in entries if e.get("status") == "reviewed" and e.get("reviewer_verdict") != "remove"}
    return ok, len(entries) - len(ok)


def load_data(store_path: Path = STORE_PATH, supplement_path: Path = SUPPLEMENT_PATH) -> Data:
    sup, pending = load_supplement(supplement_path)
    return Data(load_store(store_path), sup, pending)


def _supplement_level(e: dict) -> str:
    lv = e.get("reviewer_severity") or e.get("proposed_severity") or "unknown"
    return lv if lv in RANK else "unknown"  # "unclassified" -> unknown


def check(a: str | None, b: str | None, data: Data) -> Result:
    """a, b: formulary generics of interaction_ready medicines, or None when a medicine is not interaction_ready. Order does not matter."""
    if a is None or b is None:
        return Result(UNCONFIRMED)
    if data.store is None:
        return Result(DB_MISSING)
    best: Result | None = None
    for x in components(a):
        for y in components(b):
            e = data.store.get(pair_key(x, y)) if x != y else None
            if e and (best is None or RANK[e["severity"]] > RANK[best.level]):
                best = Result(FOUND, e["severity"], "ddinter")
    s = data.supplement.get(pair_key(a, b))
    if s and (best is None or RANK[_supplement_level(s)] > RANK[best.level]):
        best = Result(FOUND, _supplement_level(s), "curated_reviewed")
    return best or Result(NO_RECORD)
