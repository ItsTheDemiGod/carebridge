"""Read-only access to data/reference/formulary.json for the medicine picker. Case-insensitive prefix or substring matching only: no fuzzy
matching, no model, no user content stored. The formulary is UNVERIFIED until a pharmacist reviews it (the status travels with every response)."""
import json
import re
from functools import lru_cache

from app.services.guards import REPO

PATH = REPO / "data" / "reference" / "formulary.json"


def slug(generic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", generic.lower()).strip("-")


@lru_cache
def _load() -> tuple[str, dict[str, dict]]:
    raw = json.loads(PATH.read_text(encoding="utf-8"))
    entries = {}
    for m in raw["medicines"]:
        e = {"id": slug(m["generic_name"]), "generic": m["generic_name"], "brand_names": list(m["brand_names"]), "available_strengths": list(m["available_strengths"]),
             "form": m["form"], "route": m["route"]}
        assert e["id"] not in entries, f"duplicate formulary id {e['id']}"
        entries[e["id"]] = e
    return raw["verification_status"], entries


def status() -> str:
    return _load()[0]


def get(fid: str) -> dict | None:
    return _load()[1].get(fid)


def all_entries() -> list[dict]:
    return list(_load()[1].values())


def search(q: str, limit: int = 20) -> list[dict]:
    """Prefix matches first, then substring matches; within each group the formulary order. An empty query returns nothing."""
    q = q.strip().lower()
    if not q:
        return []
    prefix, inside = [], []
    for e in all_entries():
        names = [e["generic"].lower(), *(b.lower() for b in e["brand_names"])]
        if any(n.startswith(q) or any(w.startswith(q) for w in re.split(r"[\s+/-]+", n)) for n in names):
            prefix.append(e)
        elif any(q in n for n in names):
            inside.append(e)
    return (prefix + inside)[:max(1, min(limit, 20))]
