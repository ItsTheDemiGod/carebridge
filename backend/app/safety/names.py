"""Formulary generic -> DDInter component names. The ONLY name mapping used by the interaction lookup (no fuzzy matching).
Combination products are explicit in the formulary ("A + B"): each component is checked. A few components use DDInter's own spelling."""
import json
from functools import lru_cache

from app.services.guards import REPO

FORMULARY = REPO / "data" / "reference" / "formulary.json"
# formulary spelling -> DDInter spelling(s); salt forms and INN/USAN synonyms, Vitamin D3 = cholecalciferol
RENAME = {
    "Aspirin": ["Acetylsalicylic acid"], "Paracetamol": ["Acetaminophen"], "Torsemide": ["Torasemide"], "Metoprolol succinate": ["Metoprolol"],
    "Calcium carbonate + Vitamin D3": ["Calcium carbonate", "Cholecalciferol"],
}


@lru_cache
def formulary_generics() -> tuple[str, ...]:
    return tuple(m["generic_name"] for m in json.loads(FORMULARY.read_text(encoding="utf-8"))["medicines"])


@lru_cache
def _by_lower() -> dict[str, str]:
    return {g.lower(): g for g in formulary_generics()}


def canonical(generic: str | None) -> str | None:
    """Formulary spelling of a generic (case-insensitive exact match through the formulary only; no fuzzy matching), else None."""
    return _by_lower().get(generic.strip().lower()) if generic else None


def components(generic: str) -> list[str]:
    """Lowercased DDInter component names of a formulary generic; [] if the generic is not in the formulary."""
    g = canonical(generic)
    if g is None:
        return []
    return [c.lower() for c in RENAME.get(g) or [x.strip() for x in g.split(" + ")]]
