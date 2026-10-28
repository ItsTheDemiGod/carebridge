"""Phase 8a follow-up: hosted-build wording. Every ui.hosted.alt.<rest> replaces an existing ui.<rest>; none promises an upload, photo processing or reading the visitor's own document; none claims nothing at all is sent."""
import re

from app.services import templates as T

UI = {tid: v for tid, v in T.load()["strings"].items() if tid.startswith("ui.")}
ALT = {k: v for k, v in UI.items() if k.startswith("ui.hosted.alt.")}


def test_every_alt_replaces_an_existing_string_with_the_same_placeholders():
    assert len(ALT) >= 10
    for k, v in ALT.items():
        base = "ui." + k[len("ui.hosted.alt."):]
        assert base in UI, k
        for lang in ("en", "ta", "hi"):
            assert set(re.findall(r"\{(\w+)\}", v[lang]["text"])) == set(re.findall(r"\{(\w+)\}", UI[base][lang]["text"])), (k, lang)


def test_hosted_english_never_says_nothing_at_all_is_sent_and_every_hosted_text_says_where_the_real_app_is():
    hosted = {k: v for k, v in UI.items() if k.startswith("ui.hosted.")}
    for k, v in hosted.items():
        text = v["en"]["text"]
        assert not re.search(r"nothing at all|nothing is sent anywhere|nothing is requested|nothing is sent to external", text, re.I), k
    for k in ("ui.hosted.alt.steps.1.body", "ui.hosted.alt.how.n1.body", "ui.hosted.alt.privacy.local.body"):
        assert "hosted sample" in UI[k]["en"]["text"] and "real app" in UI[k]["en"]["text"]
    gh = UI["ui.hosted.pp.github"]["en"]["text"]
    assert all(w in gh for w in ("GitHub Pages", "log visits", "no cookies", "no analytics", "nothing from other sites"))
