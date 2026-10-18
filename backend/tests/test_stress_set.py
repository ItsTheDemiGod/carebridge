"""Phase 7a: the safety stress set builder and evaluation (mini synthetic interaction store, temp folders, mocked provider; no model, no DDInter data)."""
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from app.safety import interactions as I
from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import from_ground_truth
from app.services.guards import REPO
from tests.apihelpers import FakeOllama

sys.path.insert(0, str(REPO / "data"))
sys.path.insert(0, str(REPO))
import build_stress_set as B  # noqa: E402
from eval.stress import run_safety_stress as S  # noqa: E402


def mini_data() -> I.Data:
    """A fabricated store over the oral formulary drugs: roughly a third of the pairs have a record (some major, some moderate), a few more are supplement-only."""
    drugs = B.oral_generics()
    store, sup = {}, {}
    pairs = [(a, b) for k, a in enumerate(drugs) for b in drugs[k + 1:]]
    for n, (a, b) in enumerate(pairs):
        if n % 3 == 0:
            store[I.pair_key(a, b)] = {"severity": ["major", "moderate", "moderate", "minor", "unknown"][n % 5]}
        elif n % 41 == 1:
            sup[I.pair_key(a, b)] = {"status": "author_checked", "proposed_severity": "unknown", "drug_a": a, "drug_b": b}
    return I.Data(store, sup, 0)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("stress")
    manifest = B.build_all(mini_data(), out)
    return out, manifest


def test_ten_categories_three_documents_each(built):
    _, m = built
    from collections import Counter
    assert Counter(d["category"] for d in m) == {c: 3 for c in B.CATEGORIES} and len(m) == 30


def test_build_is_deterministic(built, tmp_path):
    out, m = built
    m2 = B.build_all(mini_data(), tmp_path)
    assert m == m2
    for d in m:
        for sub, ext in (("synthetic", "txt"), ("ground_truth", "json")):
            assert (out / sub / f"{d['id']}.{ext}").read_bytes() == (tmp_path / sub / f"{d['id']}.{ext}").read_bytes()


def test_ground_truth_validates_spans_match_and_names_are_formulary(built):
    out, m = built
    names = {g.lower() for g in B.G.BY_GENERIC} | {b.lower() for f in B.G.BY_GENERIC.values() for b in f["brand_names"]}
    for d in m:
        text = (out / "synthetic" / f"{d['id']}.txt").read_text(encoding="utf-8")
        gt = ExtractedDocument.model_validate_json((out / "ground_truth" / f"{d['id']}.json").read_text(encoding="utf-8"))
        for med in gt.medications:
            assert text[med.source_span.start:med.source_span.end] == med.source_span.text
            if d["category"] not in ("eye_drop_od", "garbled_name"):
                assert any((n or "").lower() in names for n in (med.brand_name, med.generic_name)), (d["id"], med.brand_name, med.generic_name)
        assert "All details are fictional" in text


def test_manifest_holds_no_interaction_levels_or_statuses(built):
    out, _ = built
    raw = (out / "manifest.json").read_text(encoding="utf-8").lower()
    for banned in ("major", "moderate", "interaction_found", "severity", "ddinter"):
        assert banned not in raw.replace("major_pair", "").replace("moderate_pair", "").replace("ddinter-derived store", "").replace("interaction levels are not stored", ""), banned


def test_garbled_names_are_near_misses_never_exact(built):
    out, m = built
    from app.normalisation.names import index, key
    from app.services.normalisation import normalise_document
    for d in (x for x in m if x["category"] == "garbled_name"):
        gt = ExtractedDocument.model_validate_json((out / "ground_truth" / f"{d['id']}.json").read_text(encoding="utf-8"))
        nd = normalise_document(from_ground_truth(gt))
        assert any({"near_miss_name", "unresolved_name"} & set(x.flags) for x in nd.medications), d["id"]
        assert not nd.medications[0].interaction_ready


def test_ground_truth_mode_invariants_hold_on_the_mini_store(built):
    out, _ = built
    r = S.gt_mode(mini_data(), out)
    assert r["invariants"]["failed"] == 0, r["invariants"]["cases"]
    assert r["documents"] == 30 and r["model_calls"] == 0
    assert r["categories"]["control"]["statuses"].get("interaction_found", 0) == 0
    assert r["categories"]["duplicate"]["duplicates_flagged"] >= 3
    assert r["categories"]["garbled_name"]["statuses"].get("not_checked_unconfirmed", 0) > 0


def test_ground_truth_mode_reports_a_broken_invariant(built):
    out, _ = built
    # an empty store: the designed pairs have no record -> the pair categories must fail I6, nothing is hidden
    r = S.gt_mode(I.Data({}, {}, 0), out)
    assert r["invariants"]["failed"] > 0 and any(c["invariant"] == "I6" for c in r["invariants"]["cases"])


class Perfect(FakeOllama):
    def __init__(self, root, docs):
        super().__init__()
        self.root, self.docs = root, list(docs)

    def generate(self, system, parts, schema, temperature=0.0):
        d = self.docs.pop(0)
        self.output = from_ground_truth(ExtractedDocument.model_validate_json((self.root / "ground_truth" / f"{d}.json").read_text(encoding="utf-8")))
        return super().generate(system, parts, schema, temperature)


def test_extraction_mode_with_a_mocked_provider(built):
    out, m = built
    for cond in ("clean",):
        (out / "rendered" / cond).mkdir(parents=True, exist_ok=True)
        for d in m:
            Image.new("L", (4, 4), 128).save(out / "rendered" / cond / f"{d['id']}.png")
    r = S.extraction_mode(mini_data(), out, Perfect(out, [d["id"] for d in m]), ("clean",))
    c = r["conditions"]["clean"]["counts"]
    assert r["conditions"]["clean"]["skipped"] == [] and c["documents"] == 30
    assert c["detected"] == c["gt_medicines"] and c.get("hallucinated", 0) == 0
    # a perfect extraction cannot silently lose an interaction: pairs with garbled names are downgraded (covered by a flag), never silent
    assert c.get("silent_not_covered_by_flag", 0) == 0 and c.get("false_alarms", 0) == 0
    assert c["found"] + c.get("strict_silent_misses", 0) == c["gt_interactions"]
