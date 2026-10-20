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


def test_dev_entries_are_dev_and_the_test_section_is_the_official_run():
    assert DATA["final_test"]["run"] is True and DATA["test"]["run"] is True
    assert {e["split"] for e in DATA["entries"]} == {"dev"}
    assert {e["split"] for e in DATA["test"]["entries"]} == {"test"}
    assert DATA["test"]["source"] == B.FT_METRICS and DATA["test"]["date"] == "2026-10-20"


def test_every_test_figure_is_complete_and_equals_the_official_file():
    m = json.loads((REPO / B.FT_METRICS).read_text(encoding="utf-8"))
    ids = [e["id"] for e in DATA["test"]["entries"]]
    assert len(ids) == len(set(ids)) == 66
    assert {e["group"] for e in DATA["test"]["entries"]} == set(DATA["test"]["groups"])
    for e in DATA["test"]["entries"]:
        for k in ("id", "group", "label", "params", "measures", "value", "unit", "source", "split", "date"):
            assert k in e, (e["id"], k)
        assert e["source"] == B.FT_METRICS and e["split"] == "test" and re.fullmatch(r"\d{4}-\d\d-\d\d", e["date"])
        assert e["unit"] in ("ratio", "count", "seconds")
        if "ci" in e:  # an interval comes with its kind and contains the value (bootstrap intervals of a ratio may touch it)
            assert e["ci_kind"] in ("wilson", "bootstrap") and 0 <= e["ci"][0] <= e["ci"][1] <= 1
            if e["unit"] == "ratio":
                assert e["ci"][0] - 1e-3 <= e["value"] <= e["ci"][1] + 1e-3, e["id"]
        if "of" in e and e["unit"] == "ratio":
            assert abs(e["n"] / e["of"] - e["value"]) < 6e-4, e["id"]
        if "dev" in e and "ci" in e and e["unit"] == "ratio":
            assert e["dev_outside"] == (e["dev"] < e["ci"][0] - 5e-5 or e["dev"] > e["ci"][1] + 5e-5)
    by = {e["id"]: e for e in DATA["test"]["entries"]}
    # spot-check against the official file itself (never a typed number)
    assert by["t_f1_norm"]["value"] == m["extraction"]["normalised"]["all"]["med_f1"]
    assert by["t_every_raw"]["value"] == m["extraction"]["raw"]["all"]["med_fully_correct_rate"]
    assert by["t_wrongsched"]["value"] == m["flags"]["all"]["wrong_schedule"] and by["t_wrongsched"]["of"] == m["flags"]["all"]["schedule_ready"]
    assert by["t_strict"]["value"] == m["safety"]["safety"]["silent_misses_strict"]
    assert by["t_ver_ta_all"]["value"] == m["explanation"]["verified_share"]["ta"]["all"]
    assert by["t_att"]["value"] == m["operational"]["all"]["attempted"] and by["t_skip"]["value"] == m["operational"]["all"]["skipped"]


def test_no_unfavourable_primary_metric_is_left_out():
    """Every protocol group is there in full: 15 measures x raw/normalised, the 8 flag/readiness measures, 3 + 5 safety, 12 + 3 explanation, 5 operational."""
    g = {k: sum(e["group"] == k for e in DATA["test"]["entries"]) for k in DATA["test"]["groups"]}
    assert g == {"ex_raw": 15, "ex_norm": 15, "flags": 8, "safety": 8, "expl": 15, "ops": 5}
    ids = {e["id"] for e in DATA["test"]["entries"]}
    assert {"t_wrongsched", "t_nameunfl", "t_wrongid", "t_strict", "t_silent", "t_false", "t_hall_raw", "t_brand_name_raw", "t_ver_ta_warning", "t_skip"} <= ids


def test_every_string_id_exists_and_every_placeholder_is_filled():
    tp = {**DATA["test"]["params"], **{"v": 0, "field": "", "lang": "", "kind": "", "cond": "", **DATA["test"]["also"]}}
    for e in DATA["test"]["entries"]:
        for key in ("label", "measures"):
            assert e[key] in UI, f"{e['id']}: missing string {e[key]}"
            for lang in ("en", "ta", "hi"):
                missing = set(PLACEHOLDER.findall(UI[e[key]][lang]["text"])) - set(tp)
                assert not missing, (e["id"], key, lang, missing)
        for v in e["params"].values():  # params that name another string
            assert not str(v).startswith("ui.") or v in UI, v
    for k, d in {"ex_raw": "ex", "ex_norm": "ex", "flags": "flags", "safety": "safety", "expl": "expl", "ops": "ops"}.items():
        assert f"ui.testing.t.g.{k}" in UI and f"ui.testing.t.d.{d}" in UI
    for tid in [x for x in UI if x.startswith("ui.testing.t.")] + ["ui.testing.limits.l9"]:
        for lang in ("en", "ta", "hi"):
            assert set(PLACEHOLDER.findall(UI[tid][lang]["text"])) <= set(tp) | set(DATA["limits_params"]) | {"date"}, tid
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
    for k in range(1, 11):
        for lang in ("en", "ta", "hi"):
            assert set(PLACEHOLDER.findall(UI[f"ui.testing.limits.l{k}"][lang]["text"])) <= set(DATA["limits_params"]) | set(DATA["test"]["params"])


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


def test_the_builder_refuses_when_the_official_results_were_changed(monkeypatch, tmp_path):
    import shutil
    shutil.copytree(REPO / B.FT, tmp_path / B.FT)
    monkeypatch.setattr(B, "REPO", tmp_path)
    B.verify_final_folder()  # a faithful copy passes
    (tmp_path / B.FT / "figures.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        B.verify_final_folder()
