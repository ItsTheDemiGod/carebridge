"""One-off (2026-10-16): adds `basis` to each drafted supplement entry and says so in the summary when the source only gives a class-level statement."""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[2] / "data" / "reference" / "interactions_supplement.json"
SPECIFIC = {"S02", "S03", "S06", "S11", "S12"}  # the source names the other drug of the pair
NOTE = " This comes from a class-level statement in the source, so both drugs must be confirmed as members of that class."
doc = json.loads(P.read_text(encoding="utf-8"))
for e in doc["entries"]:
    e["basis"] = "pair_specific_label" if e["pair_id"] in SPECIFIC else "class_statement_applied"
    if e["basis"] == "class_statement_applied" and NOTE not in e["summary_en"]:
        e["summary_en"] += NOTE
P.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print({b: sum(e["basis"] == b for e in doc["entries"]) for b in ("pair_specific_label", "class_statement_applied")})
