"""Phase 6d: data of the "How we tested it" page (scripts/build_testing_page_data.py). Reads committed metrics files only."""
import json
import re
import sys

import pytest

from app.services import templates as T
from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import build_testing_page_data as B  # noqa: E402

UI = {tid: v for tid, v in T.load()["strings"].items() if tid.startswith("ui.")}
DATA = json.loads(B.OUT.read_text(encoding="utf-8"))
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def test_generated_file_is_up_to_date():
    assert B.OUT.read_text(encoding="utf-8") == B.render(B.build()), "run: python scripts/build_testing_page_data.py"


def test_every_entry_is_complete_and_points_at_a_committed_file():
    committed = set(__import__("subprocess").run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split())
    ids = [e["id"] for e in DATA["entries"]]
    assert len(ids) == len(set(ids))
    for e in DATA["entries"]:
        for k in ("id", "group", "label", "value", "unit", "source", "measures", "data", "params", "caveat", "split", "date"):
            assert k in e, (e["id"], k)
        assert e["unit"] in ("ratio", "count") and e["split"] in ("dev", "test")
        assert e["source"] in B.SOURCES and (REPO / e["source"]).exists()
        if committed:  # a source that is not tracked would make the page unreproducible
            assert e["source"] in committed, f"{e['source']} is not committed"
        assert re.fullmatch(r"\d{4}-\d\d-\d\d", e["date"])
        if e["unit"] == "ratio":
            assert 0 <= e["value"] <= 1
        assert e["group"] in DATA["groups"]


def test_only_dev_figures_until_the_final_test_run():
    assert DATA["final_test"]["run"] is False
    assert {e["split"] for e in DATA["entries"]} == {"dev"}


def test_every_string_id_exists_and_every_placeholder_is_filled():
    for e in DATA["entries"]:
        params = {**e["params"], **DATA["limits_params"], **({"n": e["n"]} if "n" in e else {})}
        for key in ("label", "measures", "data", "caveat"):
            if e[key] is None:
                continue
            assert e[key] in UI, f"{e['id']}: missing string {e[key]}"
            for lang in ("en", "ta", "hi"):
                missing = set(PLACEHOLDER.findall(UI[e[key]][lang]["text"])) - set(params)
                assert not missing, (e["id"], key, lang, missing)
    for g in DATA["groups"]:
        assert f"ui.testing.g.{g}" in UI
    for k in range(1, 8):
        for lang in ("en", "ta", "hi"):
            assert set(PLACEHOLDER.findall(UI[f"ui.testing.limits.l{k}"][lang]["text"])) <= set(DATA["limits_params"])


def test_no_number_is_typed_into_a_testing_string():
    # digits belong to the data file; a digit in a string would be an uncommitted number (the stress/dev counts are placeholders)
    for tid, v in UI.items():
        if tid.startswith("ui.testing."):
            assert not re.search(r"\d", v["en"]["text"].replace("F1", "")), (tid, v["en"]["text"])  # "F1" is the name of the score


def test_the_claims_in_the_text_hold_in_the_data():
    by = {e["id"]: e for e in DATA["entries"]}
    assert by["fl_name"]["value"] == 0 and by["fl_name"]["of"] > 0  # "no wrong medicine name reached the user unflagged"
    assert by["sf_silent"]["value"] == 0 and by["sf_false"]["value"] == 0
    assert by["live_flows"]["n"] == by["live_flows"]["of"]
    assert by["ex_f1_raw"]["value"] < by["ex_f1_norm"]["value"] and by["inv_raw"]["value"] > by["inv_norm"]["value"]


def test_the_builder_stops_when_a_source_or_field_is_missing(monkeypatch):
    monkeypatch.setattr(B, "load", lambda p: {} if p != B.LIVE else [])
    with pytest.raises(SystemExit):
        B.build()


def test_the_builder_refuses_to_run_after_a_test_split_run_was_logged(monkeypatch, tmp_path):
    log = tmp_path / "test_runs.log"
    log.write_text("x")
    monkeypatch.setattr(B, "TEST_LOG", log)
    with pytest.raises(SystemExit):
        B.build()
