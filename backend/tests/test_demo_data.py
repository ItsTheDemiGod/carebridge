"""Phase 6d: the sample-mode fixtures (scripts/build_demo_data.py). Synthetic dev document only; no model is ever called."""
import json
import sys

import pytest

from app.schemas.confirmation import Confirmations
from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import build_demo_data as B  # noqa: E402

FIX = B.OUT
MAX_DDINTER_PAIRS = 6  # docs/DDINTER_COVERAGE.md: the demo excerpt (level and pair names only)
ALLOWED_DDINTER_KEYS = {"a", "b", "generic_a", "generic_b", "level", "same_medicine", "source", "status"}


def _load(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built(request):
    if not B.IMAGE.exists() or not (REPO / "data" / "cache").exists():
        pytest.skip("data/rendered and data/cache are gitignored local artefacts (python data/render_documents.py and the dev runs); the builder needs them")
    mp = pytest.MonkeyPatch()
    # no model call of any kind may happen: both real adapters raise, and the builder uses replay/cache-only stand-ins
    from app.llm.gemini import GeminiProvider
    from app.llm.ollama import OllamaProvider

    def boom(*a, **k):
        raise AssertionError("a model was called while building the demo data")

    mp.setattr(OllamaProvider, "generate", boom)
    mp.setattr(GeminiProvider, "generate", boom)
    first = B.render(B.build())
    second = B.render(B.build())
    request.addfinalizer(mp.undo)
    return first, second


def test_builder_is_deterministic(built):
    assert built[0] == built[1]


def test_builder_calls_no_model_and_matches_committed_fixtures(built):
    # the builder ran with both adapters raising (see the fixture); the committed files equal a fresh build
    for name, text in built[0].items():
        assert (FIX / name).read_text(encoding="utf-8") == text, f"stale {name}: python scripts/build_demo_data.py"
    assert {p.name for p in FIX.glob("*.json")} == set(built[0])


def test_every_fixture_has_the_provenance_header():
    for f in FIX.glob("*.json"):
        m = json.loads(f.read_text(encoding="utf-8"))["_meta"]
        assert m["synthetic"] is True and m["split"] == "dev" and m["source_document"] == B.DOC_ID and m["condition"] == B.CONDITION
        assert m["script_version"] == B.SCRIPT_VERSION and m["built_on"] == B.BUILT_ON


def test_source_document_is_dev_and_not_in_test_split():
    docs = {d["id"]: d["split"] for d in json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]}
    assert docs[B.DOC_ID] == "dev"


def test_scripted_decisions_are_a_valid_confirmation_request_and_follow_the_rules():
    c = Confirmations.model_validate(_load("scripted_decisions")["data"])
    acts = {d.index: d.action for d in c.decisions}
    med = _load("medicines_before_en")["data"]["medicines"]
    assert len(acts) == len(med)
    for m in med:  # every name reason is resolved by picking the formulary drug, never by an acknowledgement
        if any(r["kind"] == "name" for r in m["reasons"]):
            assert acts[m["index"]] == "select_formulary_drug"
    after = _load("confirm_response")["data"]
    assert after["confirmed"] is True


def test_fixtures_cover_every_language_before_and_after_and_the_sample_shows_a_flagged_name():
    for lang in B.LANGS:
        assert _load(f"result_before_{lang}")["data"]["confirmed"] is False
        assert _load(f"result_after_{lang}")["data"]["confirmed"] is True
        assert _load(f"strings_{lang}")["data"]["strings"]
    med = _load("medicines_before_en")["data"]["medicines"]
    assert len(med) >= 3 and any(m["review_level"] == "must_confirm" for m in med)
    assert any("select_formulary_drug" in m["allowed_actions"] and any(r["kind"] == "name" for r in m["reasons"]) for m in med)
    assert "Netfornin" in {m["as_written"]["brand"] for m in med}


def _ddinter_dicts(x, out):
    if isinstance(x, dict):
        if x.get("source") == "ddinter":
            out.append(x)
        for v in x.values():
            _ddinter_dicts(v, out)
    elif isinstance(x, list):
        for v in x:
            _ddinter_dicts(v, out)
    return out


def test_ddinter_excerpt_is_limited_to_a_few_pairs_and_the_allowed_fields():
    found = []
    for f in FIX.glob("*.json"):
        _ddinter_dicts(json.loads(f.read_text(encoding="utf-8")), found)
    assert found, "the sample is expected to show interactions"
    assert {(d["generic_a"], d["generic_b"]) for d in found}.__len__() <= MAX_DDINTER_PAIRS
    for d in found:
        assert set(d) <= ALLOWED_DDINTER_KEYS, f"DDInter field outside the allowed excerpt: {set(d) - ALLOWED_DDINTER_KEYS}"
    text = "".join(f.read_text(encoding="utf-8") for f in FIX.glob("*.json")).lower()
    for banned in ("mechanism", "ddinter_id", "ddinter id", "management", "\"description\""):
        assert banned not in text, banned


def test_the_attribution_line_is_part_of_every_result_that_shows_interactions():
    for lang in B.LANGS:
        for k in ("before", "after"):
            ids = {l["line_id"] for s in _load(f"result_{k}_{lang}")["data"]["explanation"]["sections"] for l in s["lines"]}
            assert "safety-attribution" in ids
