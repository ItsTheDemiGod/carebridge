"""Phase 7c-lite: the stress section of "How we tested it" (scripts/build_testing_page_data.py, stress_section). Figures come from eval/results/stress-extraction-v1 only."""
import json
import re
import shutil
import subprocess
import sys

import pytest

from app.services import templates as T
from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import build_testing_page_data as B  # noqa: E402

UI = {tid: v for tid, v in T.load()["strings"].items() if tid.startswith("ui.")}
S = json.loads(B.OUT.read_text(encoding="utf-8"))["stress_ext"]
M = json.loads((REPO / B.SS_METRICS).read_text(encoding="utf-8"))
PH = re.compile(r"\{(\w+)\}")
REQUIRED = {"p1", "p2", "p3", "p4", "precision_raw", "recall_raw", "f1_raw", "precision_normalised", "recall_normalised", "f1_normalised", "hall", "review_must_confirm", "review_note", "review_none",
            "found", "found_right", "strict", "unconf", "other", "false", "dup", "nondaily", "eye_od", "eye_sched", "unusual", "garbled", "garbled_ready", "ov_equal", "ov_newly", "ov_false", "failed"}


def test_every_pre_registered_metric_is_shown_for_both_conditions():
    ids = [e["id"] for e in S["entries"]]
    assert len(ids) == len(set(ids)) and REQUIRED <= set(ids)
    assert {f"{k}_{lv}" for k in ("gt", "fd") for lv in ("major", "moderate", "minor", "unknown")} <= set(ids)
    assert S["conditions"] == ["clean", "photo"] and all(set(e["cells"]) == {"clean", "photo"} for e in S["entries"])


def test_every_figure_has_source_measure_data_split_interval_and_date():
    committed = set(subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split())
    assert S["date"] == json.loads((REPO / B.SS / "run_manifest.json").read_text(encoding="utf-8"))["environment"]["started"][:10]
    for e in S["entries"]:
        assert e["split"] == "stress" and e["source"] == B.SS_METRICS and (REPO / e["source"]).exists()
        if committed:
            assert e["source"] in committed
        assert re.fullmatch(r"\d{4}-\d\d-\d\d", e["date"]) and e["group"] in S["groups"]
        for c in e["cells"].values():
            if e.get("no_kn"):
                assert c["bootstrap"] is not None  # F1 has no k of n: its interval is the document bootstrap
            else:
                assert c["n"] and c["wilson"] and c["wilson"][0] <= c["value"] <= c["wilson"][1] and c["k"] <= c["n"]
    assert "ui.testing.split.stress" in UI and "ui.testing.s.d.all" in UI


def test_every_string_exists_and_every_placeholder_is_filled():
    gp = {**S["params"], **S["also"], "date": S["date"]}
    for e in S["entries"]:
        row = {**gp, **{k: "" for k in e["params"]}}
        for key in ("label", "measures"):
            assert e[key] in UI, f"{e['id']}: {e[key]}"
            for lang in ("en", "ta", "hi"):
                assert set(PH.findall(UI[e[key]][lang]["text"])) <= set(row), (e["id"], key, lang)
        for v in e["params"].values():
            assert v in UI
    for tid in [x for x in UI if x.startswith("ui.testing.s.")] + ["ui.testing.split.stress"]:
        for lang in ("en", "ta", "hi"):
            assert set(PH.findall(UI[tid][lang]["text"])) <= set(gp) | {"level"}, (tid, lang)
            assert UI[tid]["ta" if lang != "hi" else "hi"]["review_status"] == "draft_unreviewed" or lang == "en"
    for g in S["groups"]:
        assert f"ui.testing.s.g.{g}" in UI
    for c in S["conditions"]:
        assert f"ui.testing.s.col_{c}" in UI


def test_figures_equal_the_committed_metrics_file_and_nothing_unfavourable_is_left_out():
    by = {e["id"]: e["cells"] for e in S["entries"]}
    for c in S["conditions"]:
        p = M["conditions"][c]["pooled"]
        assert by["found"][c]["k"] == p["found_rate"]["k"] and by["found"][c]["n"] == p["found_rate"]["n"]
        assert by["precision_raw"][c]["bootstrap"] == p["precision_raw"]["bootstrap95"]
        assert by["unconf"][c]["k"] == p["counts"]["unconfirmed"]
    crit = {e["id"]: e for e in S["entries"] if e["group"] == "crit"}
    assert [crit[k]["passed"] for k in ("p1", "p2", "p3", "p4")] == [v["passed"] for k, v in M["criteria"].items() if k.startswith("P")]
    assert by["garbled"]["photo"]["k"] < by["garbled"]["photo"]["n"] and by["ov_false"]["photo"]["k"] > 0 and by["unconf"]["clean"]["k"] > 0


def test_no_number_or_forbidden_word_is_typed_into_a_stress_string():
    forbidden = re.compile(r"\b(safe|safely|guaranteed?|accurate|accurately|accuracy|certified|clinically validated|doctor-approved|reliable|validated|pharmacist|native speaker)\b", re.I)
    for tid, v in UI.items():
        if tid.startswith("ui.testing.s.") or tid == "ui.testing.split.stress":
            assert not re.search(r"\d", v["en"]["text"].replace("F1", "")), tid  # "F1" is the name of the score
            assert not forbidden.search(v["en"]["text"]), tid


def test_the_builder_refuses_when_the_stress_results_were_changed(monkeypatch, tmp_path):
    shutil.copytree(REPO / B.SS, tmp_path / B.SS)
    monkeypatch.setattr(B, "REPO", tmp_path)
    B.verify_stress_folder()
    f = tmp_path / B.SS / "per_document.csv"
    f.chmod(0o666)  # the committed results are read-only
    f.write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        B.verify_stress_folder()
