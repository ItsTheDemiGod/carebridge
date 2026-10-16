"""Phase 3e: trust labels, phrase library content rules, strict matcher, pipeline order."""

import re
import tempfile

import pytest
from test_explain import FakeModel, doc
from app.schemas.extraction_output import Confidence, OutFollowUp, OutRedFlag
from app.schemas.explanation import LangText, label_key
from app.services import narrative as nv
from app.services import phrase_match as pm
from app.services import templates as T
from app.services import verification as vf
from app.services.explain import build_explanation, model_items, narrative_items

LIB = pm.library()["phrases"]
BY_ID = {p["id"]: p for p in LIB}


# ---------------- labels
@pytest.mark.parametrize("prov,rs,want", [
    ("template", "reviewed", "native_reviewed"), ("template", "draft_unreviewed", "draft_unreviewed"), ("template", "not_required", None),
    ("phrase_library", "reviewed", "native_reviewed"), ("phrase_library", "draft_unreviewed", "draft_unreviewed"), ("phrase_library", "not_required", None),
    ("model_checked", "reviewed", "machine_checked"), ("model_checked", "draft_unreviewed", "machine_checked"), ("model_checked", "not_required", "machine_checked"),
    ("original_only", "reviewed", "original_only"), ("original_only", "draft_unreviewed", "original_only"), ("original_only", "not_required", "original_only"),
])
def test_label_key_for_every_provenance_and_review_status(prov, rs, want):
    assert label_key(prov, rs) == want
    assert LangText(text="x", status="verified", provenance=prov, review_status=rs).label_key == want


def test_model_written_text_never_carries_a_human_review_label():
    for rs in ("reviewed", "draft_unreviewed", "not_required"):
        assert label_key("model_checked", rs) != "native_reviewed"
    text = "Avoid direct sunlight on weekends."
    nd = doc(follow_ups=[], red_flags=[OutRedFlag(text=text, source_quote="q", confidence=Confidence.high)], diet_activity_advice=[])
    _, _, ex = _run(FakeModel(plain={"warning-0": text}, back={"warning-0": text}), nd)
    t = ex.lines("warning")[0].text
    assert {lg: x.provenance for lg, x in t.items()} == {"en": "model_checked", "ta": "model_checked", "hi": "model_checked"}
    assert all(x.label_key == "machine_checked" and x.review_status != "reviewed" for x in t.values())
    assert t["en"].label == T.render("label.machine_checked_en", "en") and t["ta"].label == T.render("label.machine_checked", "ta")


def test_label_templates_exist_in_all_languages_and_are_draft():
    for tid in ("label.native_reviewed", "label.draft_unreviewed", "label.machine_checked", "label.machine_checked_en"):
        assert T.review_status(tid, "ta") == T.review_status(tid, "hi") == "draft_unreviewed"
        assert all(T.render(tid, lg).strip() for lg in ("en", "ta", "hi"))
    assert T.render("label.native_reviewed", "en") == "Checked by a native speaker."
    assert T.render("label.draft_unreviewed", "en") == "Draft translation, not yet checked by a native speaker."
    assert T.render("label.machine_checked", "en") == "Automatic translation checked by software only, not by a native speaker."


# ---------------- library content rules
def test_ids_unique_and_wordings_unique():
    ids = [p["id"] for p in LIB]
    assert len(ids) == len(set(ids)) and 70 <= len(ids) <= 95
    seen = {}
    for p in LIB:
        for v, _ in pm.variants(p):
            k = pm.normalise(v)
            assert seen.setdefault(k, p["id"]) == p["id"], f"{v!r} is used by {seen[k]} and {p['id']}"
    assert len(p["english_aliases"]) <= 4 and all(len(q["english_aliases"]) <= 4 for q in LIB)


def test_all_languages_present_with_identical_placeholders():
    for p in LIB:
        assert p["kind"] in ("advice", "warning", "follow_up") and p["ta"]["review_status"] == p["hi"]["review_status"] == "draft_unreviewed"
        want = sorted(pm.PLACEHOLDER.findall(p["english"]))
        assert want in ([], ["n"]) and bool(p["slot"]) == bool(want)
        for v in p["english_aliases"]:
            assert sorted(pm.PLACEHOLDER.findall(v)) == want, (p["id"], v)
        for lg in ("ta", "hi"):
            assert p[lg]["text"].strip() and sorted(pm.PLACEHOLDER.findall(p[lg]["text"])) == want, (p["id"], lg)
        # numbers written into a phrase (not slots) must be the same in all languages
        assert re.findall(r"[0-9]+", p["english"]) == re.findall(r"[0-9]+", p["ta"]["text"]) == re.findall(r"[0-9]+", p["hi"]["text"]), p["id"]


def test_rendering_leaves_no_braces_and_passes_the_script_check():
    for p in LIB:
        n = p["slot"]["min"] if p["slot"] else None
        for lg in ("en", "ta", "hi"):
            out = pm.render(p, lg, n)
            assert "{" not in out and "}" not in out
            if lg != "en":
                assert vf.script_ok(out, lg), (p["id"], lg, vf.script_share(out, lg))


def test_no_formulary_name_in_any_phrase():
    for p in LIB:
        for text in [p["english"], *p["english_aliases"], p["ta"]["text"], p["hi"]["text"]]:
            assert not vf.names_in(text), (p["id"], vf.names_in(text), text)


def test_no_phrase_matches_the_forbidden_additions_list():
    for p in LIB:
        for v, _ in pm.variants(p):
            hits = [lbl for lbl, rx in vf.FORBIDDEN if re.search(rx, v, re.I)]
            assert not hits, (p["id"], v, hits)


def test_every_urgent_warning_keeps_an_urgency_cue_in_english_and_is_marked():
    warnings = [p for p in LIB if p["kind"] == "warning"]
    assert warnings and all(isinstance(p["urgent"], bool) for p in warnings)
    assert all("urgent" not in p for p in LIB if p["kind"] != "warning")
    for p in warnings:
        if p["urgent"]:
            for v, _ in pm.variants(p):
                assert vf.URGENCY_OUTPUT.search(v), (p["id"], v)


def test_urgent_warnings_keep_the_urgency_in_ta_hi():
    tail = {"ta": ("மருத்துவமனைக்குத் திரும்பி வரவும்", "அவசர சிகிச்சைப் பிரிவுக்குச் செல்லவும்"), "hi": ("अस्पताल वापस आएँ", "आपातकालीन विभाग में जाएँ")}
    for p in LIB:
        if p["kind"] == "warning" and p["urgent"]:
            for lg in ("ta", "hi"):
                assert any(t in p[lg]["text"] for t in tail[lg]), (p["id"], lg)
            if "immediately" in p["english"]:
                assert ("உடனடியாக" in p["ta"]["text"]) and ("तुरंत" in p["hi"]["text"]), p["id"]


NEG_TA = ("வேண்டாம்", "தவிர்க்க")
NEG_HI = ("न ", "नहीं", "से बचें")


def test_negations_survive_in_ta_and_hi():
    for p in LIB:
        if re.match(r"(Do not|Avoid)", p["english"]):
            assert any(w in p["ta"]["text"] for w in NEG_TA), (p["id"], p["ta"]["text"])
            assert any(w in p["hi"]["text"] for w in NEG_HI), (p["id"], p["hi"]["text"])


def test_negated_clause_warnings_keep_the_negation():
    p = next(p for p in LIB if "does not go down" in p["english"])
    assert "குறையவில்லை" in p["ta"]["text"] and "कम न हो" in p["hi"]["text"]
    p = next(p for p in LIB if "unable to pass urine" in p["english"])
    assert "முடியாவிட்டால்" in p["ta"]["text"] and "न कर पाएँ" in p["hi"]["text"]


def test_no_dose_or_medicine_instruction_words_in_phrases():
    bad = re.compile(r"\b(dose|dosage|tablet|tablets|pill|pills|capsule|syrup|injection|medicine|medicines|medication|mg|ml)\b", re.I)
    for p in LIB:
        assert not any(bad.search(v) for v, _ in pm.variants(p)), p["id"]


# ---------------- matcher
def test_exact_alias_and_slot_match():
    assert pm.match("Drink plenty of fluids.").how == "canonical"
    assert pm.match("  • DRINK enough   fluids ").how == "alias"
    m = pm.match("Review after 7 days")
    assert m.how == "slot" and m.n == 7 and BY_ID[m.phrase_id]["english"] == "Review after {n} days."
    assert pm.match("Review after 2 weeks.").n == 2 and pm.match("Review after 1 week.").n is None


def test_wrong_number_range_unit_or_format_does_not_match():
    for t in ["Review after 1 days.", "Review after 0 days.", "Review after 365 days.", "Review after 07 days.", "Review after 7-10 days.", "Review after 2.5 weeks.", "Review after seven days.", "Review after 7 hours.", "Review after 14 months."]:
        assert pm.match(t) is None, t


def test_negation_symptom_and_clause_differences_do_not_match():
    for t in ["Drink alcohol.", "Do not drink plenty of fluids.", "Avoid plenty of fluids.", "Return to the hospital if there is chest pain.",  # emergency phrase wording differs
              "Return to the hospital if there is no fever.", "Return to the hospital if the fever goes down.", "Return to the hospital if there is fever and chest pain.",
              "Keep the wound wet.", "Do not drink water.", "Drink plenty of fluids unless you are vomiting.", "Drink plenty of fluids, and rest.", "Review after 7 days if the wound is red."]:
        assert pm.match(t) is None, t


def test_matching_is_not_fuzzy_and_uses_no_model():
    assert pm.match("Drink plenty of fluid.") is None and pm.match("Drink plenty of liquids.") is None
    imports = [ln for ln in open(pm.__file__, encoding="utf-8") if ln.startswith(("import", "from"))]
    assert not any(w in ln for ln in imports for w in ("llm", "narrative", "ollama", "httpx"))


def test_near_miss_is_recorded_but_not_displayed():
    assert pm.match("Drink plenty of fluid.") is None
    nm = pm.near_misses("Drink plenty of fluid.")
    assert nm and nm[0].phrase_id == "adv.001" and nm[0].ratio >= pm.NEAR_MISS_RATIO
    assert pm.near_misses("Drink plenty of fluids.") == []  # exact matches are not near-misses
    nd = doc(follow_ups=[], red_flags=[], diet_activity_advice=["Drink plenty of fluid."])
    ex = build_explanation(nd, None)
    ln = ex.lines("advice")[0]
    assert ln.provenance == "original_only" and ln.text["en"].text == "Drink plenty of fluid." and "Drink plenty of fluids." not in {t.text for t in ln.text.values()}


def test_every_variant_matches_itself_and_slots_fill_in_range():
    for p in LIB:
        for v, how in pm.variants(p):
            n = p["slot"]["min"] if p["slot"] else None
            m = pm.match(v.replace("{n}", str(n)) if n else v)
            assert m and m.phrase_id == p["id"], (p["id"], v)
        if p["slot"]:
            hi = p["slot"]["max"]
            assert pm.match(p["english"].replace("{n}", str(hi))).n == hi
            assert pm.match(p["english"].replace("{n}", str(hi + 1))) is None
            assert pm.match(p["english"].replace("{n}", str(p["slot"]["min"] - 1))) is None


# ---------------- pipeline
def _run(model, nd):
    nar = nv.narrate_document(model_items(nd), model, cache_dir=tempfile.mkdtemp())
    return nd, nar, build_explanation(nd, nar)


def _nd(advice=(), warnings=(), follow=()):
    return doc(diet_activity_advice=list(advice), red_flags=[OutRedFlag(text=t, source_quote="q", confidence=Confidence.high) for t in warnings],
               follow_ups=[OutFollowUp(description=t, source_quote="q", confidence=Confidence.high) for t in follow])


class Boom:
    name, model = "boom", "boom"
    calls = 0

    def cache_tag(self):
        return "boom"

    def generate(self, *a, **k):
        Boom.calls += 1
        raise AssertionError("the model must not be called for library-matched lines")


def test_matched_lines_make_no_model_call_and_show_library_text_in_every_language():
    nd = _nd(advice=["Drink plenty of fluids."], warnings=["Return to the hospital if there is fever."], follow=["Review after 7 days."])
    assert model_items(nd) == []
    nar = nv.narrate_document(model_items(nd), Boom(), cache_dir=tempfile.mkdtemp())
    assert nar.calls() == [] and Boom.calls == 0
    ex = build_explanation(nd, nar)
    for ln in (*ex.lines("advice"), *ex.lines("warning"), *ex.lines("follow_up")):
        assert ln.provenance == "phrase_library" and ln.status == "template" and ln.display_mode == "explanation" and not ln.notices
        for lg, t in ln.text.items():
            assert t.provenance == "phrase_library" and "{" not in t.text
            assert (t.label_key, t.label is None) == ((None, True) if lg == "en" else ("draft_unreviewed", False))
    fu = ex.lines("follow_up")[0]
    assert fu.text["ta"].text.startswith("7 நாட்களுக்குப்") and fu.text["hi"].text.startswith("7 दिन बाद") and fu.text["en"].text == "Review after 7 days."
    assert ex.lines("warning")[0].text["hi"].label == T.render("label.draft_unreviewed", "hi")


def test_pipeline_order_library_then_model_then_original():
    nd = _nd(advice=["Avoid direct sunlight on weekends."], warnings=["Return to the hospital if there is fever.", "Sit upright after meals for a short time."], follow=["Review after 7 days."])
    items = model_items(nd)
    assert [i.id for i in items] == ["advice-0", "warning-1"]  # warning-0 and follow_up-0 are library lines
    model = FakeModel(plain={"advice-0": "Avoid direct sunlight on weekends.", "warning-1": "Sit up after meals."},
                      back={"advice-0": "Avoid direct sunlight on weekends.", "warning-1": "Sit up after meals."}, verdict={"warning-1": "omits_information"})
    ex = build_explanation(nd, nv.narrate_document(items, model, cache_dir=tempfile.mkdtemp()))
    provs = {ln.line_id: ln.provenance for ln in ex.lines() if ln.kind in ("advice", "warning", "follow_up")}
    assert provs == {"advice-0": "model_checked", "warning-0": "phrase_library", "warning-1": "original_only", "follow_up-0": "phrase_library"}
    fb = ex.lines("warning")[1].text["en"]
    assert fb.text == "Sit upright after meals for a short time." and fb.display_mode == "original_with_notice" and fb.label_key == "original_only"


def test_warning_count_and_must_confirm_banner_unchanged_with_library():
    nd = _nd(warnings=["Return to the hospital if there is fever.", "Do something unusual.", "Go to the emergency department immediately if there is chest pain."])
    ex = build_explanation(nd, None)
    assert len(ex.lines("warning")) == 3
    assert [ln.provenance for ln in ex.lines("warning")] == ["phrase_library", "original_only", "phrase_library"]
    m0 = ex.lines("medicine")[0]
    assert m0.review_level == "must_confirm" and m0.notices and m0.notices[0].code == "must_confirm" and not m0.settled


def test_use_library_false_restores_phase3_behaviour():
    nd = _nd(advice=["Drink plenty of fluids."])
    assert [i.id for i in model_items(nd, use_library=False)] == ["advice-0"]
    assert build_explanation(nd, None, use_library=False).lines("advice")[0].provenance == "original_only"


def test_ta_hi_keep_the_exact_digits_of_the_source_number():
    for n in (2, 14, 30):
        fu = build_explanation(_nd(follow=[f"Review after {n} days."]), None).lines("follow_up")[0]
        assert all(str(n) in t.text for t in fu.text.values())
