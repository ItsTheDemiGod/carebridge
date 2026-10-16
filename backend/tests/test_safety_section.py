import re

from medfactory import med

from app.safety import interactions as I
from app.schemas.extraction import DocumentType
from app.schemas.normalised import NormalisedDocument
from app.services import safety_section as SS
from app.services.explain import build_explanation

STORE = {"metformin|omeprazole": {"severity": "major"}, "furosemide|metformin": {"severity": "minor"}}


def m(resolved, ready=True, level="none", brand=None, **kw):
    x = med(brand=brand or resolved, resolved=resolved, level=level, **kw)
    x.interaction_ready = ready
    return x


def explain(*meds, data=None):
    nd = NormalisedDocument(document_type=DocumentType.discharge_summary, medications=list(meds))
    return build_explanation(nd, None, safety_data=data or I.Data(STORE))


def texts(doc, lang="en"):
    sec = next((s for s in doc.sections if s.id == "safety"), None)
    return [ln.text[lang].text for ln in sec.lines] if sec else []


def test_found_pairs_listed_individually_most_severe_first_and_rest_aggregated():
    d = explain(m("Metformin"), m("Omeprazole"), m("Furosemide"), m("Ramipril"), m("Atenolol"))
    t = texts(d)
    found = [x for x in t[1:] if "interact" in x and "limited database" not in x and "Interaction data" not in x]
    assert "serious" in found[0] and "Metformin" in found[0] and "Omeprazole" in found[0]
    assert "minor" in found[1].lower()
    agg = [x for x in t if "limited database" in x]
    assert len(agg) == 1 and agg[0].startswith("8 medicine pairs") and "does not mean they are safe" in agg[0]  # 10 pairs - 2 found
    assert not any(re.search(r"\bRamipril\b.*\bAtenolol\b", x) for x in t)  # per-pair detail only in the data structure
    assert d.safety.counts.pairs == 10 and t[-1].startswith("Interaction data: DDInter (CC BY-NC-SA 4.0)")


def test_banner_only_when_needed_and_never_says_safe_or_ok():
    d = explain(m("Metformin"), m("Omeprazole"))
    assert texts(d)[0].startswith("One or more possible interactions")
    d = explain(m("Metformin"), m("Ramipril"), m("Zzz", ready=False, level="must_confirm"))
    assert texts(d)[0].startswith("Some medicine details need your confirmation")
    d = explain(m("Metformin"), m("Ramipril"))
    assert d.safety.overall_state == "ok_to_review" and not any(x.startswith(("One or more", "Some medicine details")) for x in texts(d))
    for doc in (d, explain(m("Metformin"), m("Omeprazole"))):
        for lang in ("en", "ta", "hi"):
            assert not re.search(r"\bok\b|\bokay\b", " ".join(texts(doc, lang)), re.I)


def test_unconfirmed_pairs_get_their_own_aggregated_line():
    d = explain(m("Metformin"), m("Zzz", ready=False, level="must_confirm"), m("Yyy", ready=False, level="must_confirm"))
    t = texts(d)
    assert any(x.startswith("3 medicine pairs were not checked") and "name needs to be confirmed" in x for x in t)
    assert not any("limited database" in x for x in t)
    assert any(x.startswith("1 medicine pair") for x in texts(explain(m("Metformin"), m("Zzz", ready=False, level="must_confirm"))))


def test_missing_database_has_its_own_line_and_no_count():
    d = explain(m("Metformin"), m("Omeprazole"), data=I.Data(None))
    t = texts(d)
    assert any("interaction data is not available" in x for x in t) and not any("limited database" in x for x in t)


def test_duplicate_and_reminder_lines():
    d = explain(m("Metformin", brand="Glycomet"), m("Metformin", brand="Glucophage", timing="unspecified"))
    t = texts(d)
    assert any(x.startswith("Metformin appears more than once") for x in t)
    assert any("not daily or is not stated" in x for x in t)
    assert not any("limited database" in x for x in t)  # the duplicate pair is not an unchecked pair


def test_attribution_variants_and_ta_hi_are_drafts():
    d = explain(m("Metformin"), m("Omeprazole"))
    assert "not used yet" in texts(d)[-1] and "supplement reviewed" not in texts(d)[-1]
    sec = next(s for s in d.sections if s.id == "safety")
    for ln in sec.lines[:-1]:
        assert ln.text["ta"].review_status == ln.text["hi"].review_status == "draft_unreviewed"
        assert ln.text["ta"].label_key == "draft_unreviewed"


def test_medicine_must_confirm_banner_still_present_and_no_safety_section_for_one_clean_medicine():
    d = explain(m("Metformin", ready=False, level="must_confirm"))
    assert d.sections[1].lines[0].notices and any(s.id == "safety" for s in d.sections)  # banner only
    assert not any(s.id == "safety" for s in explain(m("Metformin")).sections)


def test_guardrail_failure_fails_closed(monkeypatch):
    monkeypatch.setattr(SS, "scan", lambda text, tid=None: [("reassurance", "x")])
    d = explain(m("Metformin"), m("Omeprazole"))
    assert d.guardrail_events and all("rejected by guardrail" in e for e in d.guardrail_events)
    assert "Automatic explanation not available" in texts(d)[0]
