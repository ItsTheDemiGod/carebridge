import json
import re
import tempfile

import pytest
from medfactory import med

from app.llm.base import LLMResponse
from app.schemas.extraction import DocumentType
from app.schemas.extraction_output import Confidence, OutFollowUp, OutRedFlag
from app.schemas.normalised import NormalisedDocument
from app.services import narrative as nv
from app.services import verification as vf
from app.services.explain import build_explanation, narrative_items

SRC = {
    "advice-0": "Drink 2 litres of water daily.",
    "follow_up-0": "Review after 7 days.",
    "warning-0": "Return to hospital immediately if the fever does not go down.",
    "warning-1": "Do not take Metformin on an empty stomach.",
}
TA = "இது தமிழ் உரை Metformin 2 7"  # Tamil script with Latin drug name; numbers are overridden per test


class FakeModel:
    """Scripted stand-in for the provider. `plain`, `tr`, `back`, `verdict` override the per-id output of each stage."""

    name, model = "fake", "fake-model"

    def __init__(self, plain=None, tr=None, back=None, verdict=None, drop=None, ta_ok=True):
        self.plain, self.tr, self.back, self.verdict, self.drop, self.calls = plain or {}, tr or {}, back or {}, verdict or {}, drop or {}, 0
        self.ta_ok = ta_ok

    def cache_tag(self):
        return "fake"

    def generate(self, system, parts, schema, temperature=0.0):
        self.calls += 1
        p = json.loads(parts[0].data)
        ids = [x["id"] for x in p["items"]]
        lang = p.get("language")
        if schema is nv.SimplifyOut:
            items = [{"id": i, "plain_english": self.plain.get(i, SRC[i])} for i in ids if i not in self.drop.get("simplify", ())]
        elif schema is nv.TranslateOut:
            items = [{"id": i, "text": self.tr.get((lang, i), self._native(lang, i, p))} for i in ids]
        elif schema is nv.BackOut:
            items = [{"id": i, "english": self.back.get(i, SRC[i])} for i in ids]
        else:
            items = [{"id": x["id"], "verdict": self.verdict.get(x["id"], "supported"), "reason": "scripted"} for x in p["items"]]
        return LLMResponse(text=json.dumps({"items": items}, ensure_ascii=False), usage={}, latency_s=0.01, calls=1)

    def _native(self, lang, i, p):
        plain = next(x["text"] for x in p["items"] if x["id"] == i)
        word = "இது தமிழ்" if lang == "Tamil" else "यह हिंदी है"
        body = " ".join([word] * (len(plain) // 8 + 1))  # length in proportion to the source
        return f"{body} {' '.join(re.findall(r'[0-9]+', plain))} " + " ".join(vf.names_in(plain)).title()


def doc(**over):
    base = dict(document_type=DocumentType.discharge_summary, medications=[med(level="must_confirm", flags=["unresolved_name"], sched=False), med(brand="Dolo", resolved="Paracetamol")],
                follow_ups=[OutFollowUp(description=SRC["follow_up-0"], source_quote="q", confidence=Confidence.high)],
                red_flags=[OutRedFlag(text=SRC["warning-0"], source_quote="q", confidence=Confidence.high), OutRedFlag(text=SRC["warning-1"], source_quote="q", confidence=Confidence.high)],
                diet_activity_advice=[SRC["advice-0"]])
    return NormalisedDocument(**{**base, **over})


def run(model, nd=None):
    nd = nd or doc()
    nar = nv.narrate_document(narrative_items(nd), model, cache_dir=tempfile.mkdtemp())
    return nd, nar, build_explanation(nd, nar)


def line(ex, lid):
    return next(ln for ln in ex.lines() if ln.line_id == lid)


def test_perfect_lines_are_verified_in_all_languages():
    _, nar, ex = run(FakeModel())
    assert len(nar.calls()) == 8
    for lid in SRC:
        ln = line(ex, lid)
        assert ln.status == "verified" and ln.display_mode == "explanation", (lid, [t.verification.reason for t in ln.text.values()])
        assert all(t.verification.passed and t.verification.judge_verdict == "supported" for t in ln.text.values())
        assert ln.text["ta"].review_status == "draft_unreviewed" and ln.text["hi"].review_status == "draft_unreviewed"
        assert not ln.notices


def test_changed_number_fails_deterministically_and_falls_back():
    _, _, ex = run(FakeModel(plain={"advice-0": "Drink 3 litres of water daily."}))
    ln = line(ex, "advice-0")
    en = ln.text["en"]
    assert en.status == "unverified" and en.display_mode == "original_with_notice" and en.text == SRC["advice-0"]  # original shown, not the model text
    assert not en.verification.deterministic["numbers"] and en.verification.reason.startswith("numbers:")
    assert ln.status == "unverified" and ln.notices[0].code == "fallback" and "en" in ln.notices[0].text
    assert line(ex, "follow_up-0").status == "verified"  # other lines are unaffected


def test_dropped_negation_is_caught_by_the_judge():
    nm = FakeModel(plain={"warning-1": "Take Metformin on an empty stomach."}, verdict={"warning-1": "contradicts"})
    _, _, ex = run(nm)
    t = line(ex, "warning-1").text["en"]
    assert all(t.verification.deterministic.values())  # no deterministic check can see a dropped "not"
    assert t.status == "unverified" and t.verification.judge_verdict == "contradicts" and t.verification.reason.startswith("judge: contradicts")


def test_invented_drug_name_fails_the_name_check():
    _, _, ex = run(FakeModel(plain={"advice-0": "Drink 2 litres of water daily. Take Pantoprazole."}))
    t = line(ex, "advice-0").text["en"]
    assert not t.verification.deterministic["drug_names"] and "invented ['pantoprazole']" in t.verification.reason


def test_dropped_drug_name_fails_the_name_check():
    _, _, ex = run(FakeModel(plain={"warning-1": "Do not take it on an empty stomach."}))
    assert "missing ['metformin']" in line(ex, "warning-1").text["en"].verification.reason


def test_wrong_script_tamil_fails_while_english_and_hindi_verify():
    _, _, ex = run(FakeModel(tr={("Tamil", "advice-0"): "Drink 2 litres of water daily."}))
    ln = line(ex, "advice-0")
    assert ln.text["ta"].status == "unverified" and ln.text["ta"].verification.reason.startswith("script:") and ln.text["ta"].text == SRC["advice-0"]
    assert ln.text["en"].status == "verified" and ln.text["hi"].status == "verified"
    assert ln.status == "unverified" and ln.display_mode == "original_with_notice" and list(ln.notices[0].text) == ["ta"]


def test_judge_adds_information_blocks_verification():
    _, _, ex = run(FakeModel(verdict={"follow_up-0": "adds_information"}))
    for lang in ("en", "ta", "hi"):
        t = line(ex, "follow_up-0").text[lang]
        assert t.status == "unverified" and t.verification.judge_verdict == "adds_information" and not t.verification.passed


def test_missing_id_from_the_model():
    nd, nar, ex = run(FakeModel(drop={"simplify": ("advice-0",)}))
    ln = line(ex, "advice-0")
    assert ln.status == "original_only" and ln.text["en"].verification.reason == "id_integrity: id_missing"
    assert ln.text["ta"].text == SRC["advice-0"] and ln.display_mode == "original_with_notice"
    assert line(ex, "warning-0").status == "verified"


def test_forbidden_additions_and_urgency():
    _, _, ex = run(FakeModel(plain={"warning-0": "Return to hospital if the fever does not go down.", "advice-0": "Drink 2 litres of water daily. Do not worry, this is normal."}))
    assert "forbidden_additions" in line(ex, "advice-0").text["en"].verification.reason
    assert line(ex, "warning-0").text["en"].verification.deterministic["urgency"]  # "hospital" keeps an equivalent cue
    _, _, ex2 = run(FakeModel(plain={"warning-0": "The fever may not go down."}))
    assert not line(ex2, "warning-0").text["en"].verification.deterministic["urgency"]


def test_fallback_assembly_keeps_every_warning_and_never_shows_unverified_text():
    nd = doc()
    ex = build_explanation(nd, None)  # model did not run at all
    assert len(ex.lines("warning")) == len(nd.red_flags) == 2
    for ln in ex.lines("warning") + ex.lines("advice") + ex.lines("follow_up"):
        assert ln.status == "original_only" and ln.display_mode == "original_with_notice"
        assert all(t.text == ln.source_text and t.status == "original_only" for t in ln.text.values())
        assert ln.notices[0].text["ta"].text and "{" not in ln.notices[0].text["hi"].text


def test_warning_count_equals_extracted_even_when_all_fail():
    nd = doc()
    _, _, ex = run(FakeModel(verdict={k: "contradicts" for k in SRC}), nd)
    assert [ln.source_text for ln in ex.lines("warning")] == [r.text for r in nd.red_flags]
    assert all(ln.status == "unverified" for ln in ex.lines("warning"))


def test_must_confirm_medicine_has_banner_and_is_never_settled():
    _, _, ex = run(FakeModel())
    m0, m1 = ex.lines("medicine")
    assert m0.notices[0].code == "must_confirm" and not m0.settled and m0.notices[1].code == "unresolved_name"
    assert m1.settled and not m1.notices
    assert ex.sections[0].id == "disclaimer" and "not medical advice" in ex.sections[0].lines[0].text["en"].text


def test_empty_categories_go_to_not_found():
    nd = doc(medications=[], follow_ups=[], diet_activity_advice=[])
    ex = build_explanation(nd, None)
    nf = [ln.text["en"].text for s in ex.sections if s.id == "not_found" for ln in s.lines]
    assert nf == ["Not found in the document: medicines.", "Not found in the document: follow-up visits.", "Not found in the document: diet or activity instructions."]


def test_extra_id_fails_the_whole_batch():
    class Extra(FakeModel):
        def generate(self, system, parts, schema, temperature=0.0):
            r = super().generate(system, parts, schema)
            if schema is nv.SimplifyOut:
                d = json.loads(r.text)
                d["items"].append({"id": "zz", "plain_english": "x"})
                r.text = json.dumps(d)
            return r

    _, _, ex = run(Extra())
    assert all(ln.text["en"].status == "original_only" and "extra_ids" in ln.text["en"].verification.reason for ln in ex.lines("advice") + ex.lines("warning"))


@pytest.mark.parametrize("text,lang,ok", [("Drink 2 litres", "en", True), ("நீர் குடிக்கவும் 2", "ta", True), ("पानी पिएँ 2", "hi", True), ("पानी पिएँ", "ta", False)])
def test_script_check_in_deterministic(text, lang, ok):
    res, _ = vf.deterministic("advice", "Drink 2 litres" if lang == "en" else "Drink 2", text, lang)
    assert res["script"] is ok


def test_numbers_use_unicode_digits():
    assert vf.digit_strings("௨ and 12 and ७") == {"2", "12", "7"}
