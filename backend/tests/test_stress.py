import json
import sys

from app.llm.base import LLMResponse
from app.services import narrative as nv
from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from eval.stress import run_stress as rs  # noqa: E402


class Scripted:
    """Judge says contradicts when the candidate contains '10 kg'; back-translation and simplification are the identity."""

    name, model = "fake", "fake-model"

    def cache_tag(self):
        return "fake-stress"

    def generate(self, system, parts, schema, temperature=0.0):
        p = json.loads(parts[0].data)
        if schema is nv.JudgeOut:
            items = [{"id": x["id"], "verdict": "contradicts" if "10 kg" in x["candidate"] else "supported", "reason": "scripted"} for x in p["items"]]
        elif schema is nv.BackOut:
            items = [{"id": x["id"], "english": x["text"]} for x in p["items"]]
        else:
            items = [{"id": x["id"], "plain_english": x["text"]} for x in p["items"]]
        return LLMResponse(text=json.dumps({"items": items}), usage={}, latency_s=0.01, calls=1)


def test_stress_set_shape():
    d = json.loads(rs.STRESS.read_text(encoding="utf-8"))
    en = d["english_pairs"]
    assert sum(p["label"] == "correct" for p in en) == 20 and sum(p["label"] == "wrong" for p in en) == 20
    from collections import Counter
    c = Counter(rs.GROUP.get(p["wrong_type"], p["wrong_type"]) for p in en if p["label"] == "wrong")
    assert set(c) == {"number_changed", "negation_dropped_or_flipped", "timing_swapped", "clause_dropped", "invented_advice", "urgency_softened", "item_merged", "unit_changed"} and min(c.values()) >= 2
    assert len(d["simplify_sources"]) == 15
    for lg in ("ta", "hi"):
        t = d["translation_pairs"][lg]
        assert sum(p["label"] == "correct" for p in t) == 6 and sum(p["label"] == "wrong" for p in t) == 6


def test_pair_evaluation_and_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(nv, "CACHE_DIR", tmp_path)
    pairs = [dict(id="a", kind="advice", label="correct", wrong_type=None, source="Keep the wound dry.", candidate="Keep the wound dry."),
             dict(id="b", kind="advice", label="wrong", wrong_type="number_changed", source="Lift nothing over 5 kg.", candidate="Lift nothing over 10 kg."),
             dict(id="c", kind="advice", label="wrong", wrong_type="clause_dropped", source="Keep it dry and clean.", candidate="Keep it dry and clean.")]  # undetectable by the scripted judge: a miss
    calls = []
    rows = rs.evaluate_pairs(pairs, "en", Scripted(), calls)
    s = rs.summarize_pairs(rows)
    assert s["false_reject"]["rate"] == 0.0 and s["detection"]["overall"]["combined"] == 0.5
    assert s["detection"]["by_type"]["number_changed"] == dict(n=1, deterministic=1.0, judge=1.0, combined=1.0)
    assert s["confusion"] == dict(correct=dict(verified=1, rejected=0), wrong=dict(verified=1, rejected=1)) and [x["id"] for x in s["missed"]] == ["c"]
    assert calls and all(c["type"] == "judge_en" for c in calls)


def test_simplifier_report_and_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(nv, "CACHE_DIR", tmp_path)
    r = rs.evaluate_simplifier([dict(id="s1", kind="advice", text="Ambulate three times daily.")], Scripted(), [])
    assert r["unchanged_share"] == 1.0 and r["verified_share"] == 1.0 and r["lost_or_added"] == []
    assert rs.coverage(["Drink plenty of fluids.", "Ambulate three times daily."])["matched"] == 1
