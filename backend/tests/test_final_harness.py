"""Phase 7a: the one-shot final-test harness, tested on a tiny SYNTHETIC fixture repository in a temp folder with mocked providers.
No model is called and no real test-split file is opened (asserted below by making any such open raise)."""
import argparse
import builtins
import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import from_ground_truth
from app.services.guards import REPO
from tests.apihelpers import FakeOllama

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
import freeze_manifest as FM  # noqa: E402
from eval.final_test import report as R  # noqa: E402
from eval.final_test import run_final as RF  # noqa: E402
from eval.final_test.stats import bootstrap_ci, percentile, wilson  # noqa: E402

REAL_DATA = (REPO / "data").resolve()


def _real_test_ids() -> set[str]:
    m = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]  # the manifest only says which ids are test; they are never printed
    return {d["id"] for d in m if d["split"] == "test"}


@pytest.fixture(autouse=True)
def no_real_test_files(monkeypatch):
    """Any attempt to open a real test-split document, ground truth or rendered image fails the test."""
    ids = _real_test_ids()

    def forbidden(p) -> bool:
        try:
            q = Path(p).resolve()
        except (TypeError, OSError, ValueError):
            return False
        return REAL_DATA in q.parents and any(i in q.name for i in ids) and q.suffix in (".txt", ".json", ".png", ".pdf")

    real_open, real_read_text, real_read_bytes, real_path_open = builtins.open, Path.read_text, Path.read_bytes, Path.open

    def guard(p):
        if forbidden(p):
            raise AssertionError("a real test-split file was opened")

    monkeypatch.setattr(builtins, "open", lambda f, *a, **k: (guard(f), real_open(f, *a, **k))[1])
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: (guard(self), real_read_text(self, *a, **k))[1])
    monkeypatch.setattr(Path, "read_bytes", lambda self, *a, **k: (guard(self), real_read_bytes(self, *a, **k))[1])
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: (guard(self), real_path_open(self, *a, **k))[1])


# --------------------------------------------------------------------------------------------------------- fixture repo
GT = {
    "t1": [("Glycomet", "Metformin", "500 mg", "1 tablet", 2, "after_meals")],
    "t2": [("Telma", "Telmisartan", "40 mg", "1 tablet", 1, "morning"), ("Lipitor", "Atorvastatin", "10 mg", "1 tablet", 1, "bedtime")],
    "t3": [("Crocin", "Paracetamol", "650 mg", "1 tablet", 3, "after_meals")],
}


def gt_json(meds):
    return {"document_type": "prescription", "document_language": "en", "follow_ups": [], "red_flags": [], "diet_activity_advice": [], "medications": [
        {"brand_name": b, "generic_name": g, "strength": s, "form": "tablet", "route": "oral", "dose": d,
         "frequency": {"times_per_day": n, "timing_label": t, "original_abbreviation": None, "is_prn": False}, "duration_days": 5, "duration_text": "5 days",
         "special_instructions": None, "source_span": {"start": 0, "end": 0, "text": ""}} for b, g, s, d, n, t in meds]}


def make_repo(tmp: Path) -> Path:
    r = tmp / "repo"
    docs = [{"id": i, "split": "test", "type": "prescription", "template": "x", "difficulty": "clean"} for i in GT] + [{"id": "d1", "split": "dev", "type": "prescription", "template": "x", "difficulty": "clean"}]
    files = {"data/manifest.json": json.dumps({"seed": 1, "note": "fixture", "documents": docs}), "backend/app/x.py": "X = 1\n", "eval/final_test/y.py": "Y = 1\n",
             "docs/FINAL_TEST_PROTOCOL.md": "protocol\n", "backend/requirements.txt": "x\n"}
    for i, meds in GT.items():
        files[f"data/synthetic/{i}.txt"] = "Tab " + "\nTab ".join(f"{b} {s} {d}" for b, _g, s, d, _n, _t in meds) + "\n"
        files[f"data/ground_truth/{i}.json"] = json.dumps(gt_json(meds))
    for rel, text in files.items():
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        (r / rel).write_text(text, encoding="utf-8")
    from PIL import Image
    for ci, c in enumerate(RF.CONDS[1:]):
        for ii, i in enumerate(GT):
            (r / "data/rendered" / c).mkdir(parents=True, exist_ok=True)
            Image.new("L", (4, 4), 40 + 20 * ci + 5 * ii).save(r / "data/rendered" / c / f"{i}.png")  # distinct bytes: the cache is keyed on the image
    (r / ".gitignore").write_text("eval/runs/\ndata/cache/\ndata/rendered/\n", encoding="utf-8")
    for cmd in (["init", "-q"], ["config", "user.email", "t@example.org"], ["config", "user.name", "t"], ["add", "-A"], ["commit", "-qm", "fixture"]):
        subprocess.run(["git", *cmd], cwd=r, check=True, capture_output=True)
    (r / "eval/final_test/freeze_manifest.json").write_text(json.dumps(FM.build(r, with_settings=False)), encoding="utf-8")
    (r / "eval/final_test/model_pin.json").write_text(json.dumps({"model": "m", "model_digest": "abc", "ollama_version": "9"}), encoding="utf-8")
    (r / "eval/final_test/test_data_pin.json").write_text(json.dumps({"sha256": RF.test_data_hash(r, list(GT)), "documents": 3}), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=r, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "pins"], cwd=r, check=True, capture_output=True)
    subprocess.run(["git", "tag", RF.TAG], cwd=r, check=True, capture_output=True)
    return r


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path)


def args(**kw):
    return argparse.Namespace(**{"final_test_run": True, "rerun_reason": None, **kw})


OLLAMA_OK = lambda: {"ollama_version": "9", "model": "m", "model_digest": "abc"}  # noqa: E731


def guards_for(repo, **kw):
    return lambda: RF.check_guards(repo, args(**kw), verify=lambda r: FM.verify(r, with_settings=False), ollama=OLLAMA_OK)


# ------------------------------------------------------------------------------------------------------------- refusals
def test_refuses_without_the_flag(repo):
    with pytest.raises(RF.Refusal, match="--final-test-run"):
        RF.check_guards(repo, args(final_test_run=False), verify=lambda r: [], ollama=OLLAMA_OK)


def test_refuses_with_a_dirty_tree(repo):
    (repo / "notes.txt").write_text("x")
    with pytest.raises(RF.Refusal, match="not clean"):
        guards_for(repo)()


def test_log_file_alone_does_not_make_the_tree_dirty(repo):
    RF.log_invocation(repo, "x")
    assert RF.git_is_clean(repo)


def test_refuses_on_drift_in_a_frozen_file(repo):
    (repo / "backend/app/x.py").write_text("X = 2\n")
    subprocess.run(["git", "commit", "-qam", "change"], cwd=repo, check=True, capture_output=True)  # clean tree, but a frozen file changed
    with pytest.raises(RF.Refusal, match="does not verify"):
        guards_for(repo)()


def test_refuses_without_the_tag(repo):
    subprocess.run(["git", "tag", "-d", RF.TAG], cwd=repo, check=True, capture_output=True)
    with pytest.raises(RF.Refusal, match="freeze-pre-test"):
        guards_for(repo)()


def test_tag_on_an_ancestor_is_accepted_when_the_manifest_verifies(repo):
    (repo / "NOTES.md").write_text("not frozen\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "notes"], cwd=repo, check=True, capture_output=True)
    assert guards_for(repo)()["tag_commit"]


def test_refuses_when_the_model_digest_or_test_data_differ_from_the_pin(repo):
    with pytest.raises(RF.Refusal, match="digest"):
        RF.check_guards(repo, args(), verify=lambda r: [], ollama=lambda: {"ollama_version": "9", "model": "m", "model_digest": "other"})
    (repo / "data/synthetic/t1.txt").write_text("changed\n")
    subprocess.run(["git", "commit", "-qam", "data"], cwd=repo, check=True, capture_output=True)
    with pytest.raises(RF.Refusal, match="test documents differ"):
        RF.check_guards(repo, args(), verify=lambda r: [], ollama=OLLAMA_OK)


def test_refuses_without_pins(repo):
    (repo / "eval/final_test/model_pin.json").unlink()
    subprocess.run(["git", "commit", "-qam", "x"], cwd=repo, check=True, capture_output=True)
    with pytest.raises(RF.Refusal, match="model_pin.json"):
        guards_for(repo)()


# ---------------------------------------------------------------------------------------------------- a mocked full run
class Perfect(FakeOllama):
    """Answers every extraction call with the ground truth of the document it sees (looked up from the image size marker); the fixture has no real model."""
    def __init__(self, repo):
        super().__init__()
        self.repo, self.order = repo, []

    def generate(self, system, parts, schema, temperature=0.0):
        doc = self.order.pop(0)
        self.output = from_ground_truth(ExtractedDocument.model_validate_json((self.repo / "data/ground_truth" / f"{doc}.json").read_text(encoding="utf-8")))
        return super().generate(system, parts, schema, temperature)


@pytest.fixture
def stubs(monkeypatch, repo):
    import app.services.extraction as E
    monkeypatch.setattr(E, "assert_synthetic", lambda p, *a, **k: Path(p))
    monkeypatch.setattr(RF, "stage_explanation", lambda *a, **k: 0)
    monkeypatch.setattr(RF, "explanation_metrics", lambda run_id: {"documents": 0, "provenance_share": {}, "phase3_verified_share": {}})
    monkeypatch.setattr(RF, "safety_metrics", lambda run_id: {"split": "test", "safety": {"silent_misses_strict": 0, "silent_misses_not_covered_by_a_flag": 0, "false_alarms": 0, "downgrades": 0},
                                                              "ground_truth": {"pairs": 0}, "duplicates": {}, "pairs_by_condition": {}, "share_not_checked_by_condition": {}})
    monkeypatch.setattr(R, "dev_vs_test", lambda m, root=REPO: [])

    def provider():
        p = Perfect(repo)
        p.order = [d for _c in RF.CONDS for d in sorted(GT)]
        return p
    return provider


def test_full_run_writes_checksummed_results_and_refuses_a_second_official_run(repo, stubs):
    out = RF.run(repo, args(), guards=guards_for(repo), provider_factory=stubs)
    assert out.name == RF.OFFICIAL_ID and RF.verify_checksums(out)
    m = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert m["official"] is True and m["skipped"] == [] and m["documents"] == 3
    assert m["extraction"]["normalised"]["all"]["med_f1"] == 1.0
    assert m["operational"]["all"]["attempted"] == 15 and m["operational"]["all"]["scored"] == 15
    log = (repo / "eval/test_runs.log").read_text(encoding="utf-8")
    assert "invoked" in log and "complete" in log
    with pytest.raises(RF.Refusal, match="second OFFICIAL run"):
        RF.run(repo, args(), guards=guards_for(repo), provider_factory=stubs)
    assert "REFUSED" in (repo / "eval/test_runs.log").read_text(encoding="utf-8")
    # a post-hoc re-run goes to its own folder with a label and never touches the official one
    before = (out / "metrics.json").read_bytes()
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)  # the owner commits the official results first
    subprocess.run(["git", "commit", "-qm", "official results"], cwd=repo, check=True, capture_output=True)
    out2 = RF.run(repo, args(rerun_reason="checking"), guards=guards_for(repo), provider_factory=stubs)
    assert out2.name == f"{RF.OFFICIAL_ID}-posthoc-1" and "POST-HOC" in (out2 / "metrics.md").read_text(encoding="utf-8")
    assert json.loads((out2 / "metrics.json").read_text(encoding="utf-8"))["official"] is False
    assert (out / "metrics.json").read_bytes() == before


def test_rerun_reason_is_refused_before_the_official_run_completes(repo):
    with pytest.raises(RF.Refusal, match="has not completed"):
        RF.results_dir_for(repo, "why")


def test_resume_gives_identical_results_and_a_skipped_document_is_listed(repo, stubs, monkeypatch):
    import app.services.extraction as E
    calls = {"n": 0}
    real = E.extract_document

    def flaky(path, **kw):
        calls["n"] += 1
        if calls["n"] == 7:  # one provider failure in the middle of the run
            from app.services.extraction import ExtractionResult
            return ExtractionResult(ok=False, error="context_truncated", skipped=True)
        return real(path, **kw)
    monkeypatch.setattr(E, "extract_document", flaky)
    out = RF.run(repo, args(), guards=guards_for(repo), provider_factory=stubs)
    m = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert len(m["skipped"]) == 1 and "context_truncated" in m["skipped"][0]
    assert m["operational"]["all"]["skipped"] == 1 and m["operational"]["all"]["attempted"] == 15
    # resume from the cache: the fixed provider answers the rest (cached ones are free); results are identical apart from the one document now scored
    import shutil
    shutil.rmtree(repo / "eval/results/final-test-v1")
    monkeypatch.setattr(E, "extract_document", real)
    out2 = RF.run(repo, args(), guards=guards_for(repo), provider_factory=lambda: _recording(stubs))
    m2 = json.loads((out2 / "metrics.json").read_text(encoding="utf-8"))
    assert m2["skipped"] == [] and m2["operational"]["all"]["scored"] == 15


def _recording(factory):
    p = factory()
    p.order = p.order[6:] + p.order[:6]  # the 7th call (the failed one) is the first fresh one; the rest come from the cache
    return p


def test_resume_from_cache_is_deterministic(repo, stubs):
    out = RF.run(repo, args(), guards=guards_for(repo), provider_factory=stubs)
    first = (out / "per_document.csv").read_text(encoding="utf-8")
    import shutil
    shutil.rmtree(out)
    shutil.rmtree(repo / "eval/runs")  # raw outputs gone; the cache (data/cache) alone must reproduce them
    out2 = RF.run(repo, args(), guards=guards_for(repo), provider_factory=lambda: FakeOllama())  # a provider that would give wrong answers if it were called
    assert (out2 / "per_document.csv").read_text(encoding="utf-8") == first


def test_checksum_file_detects_tampering(repo, stubs):
    out = RF.run(repo, args(), guards=guards_for(repo), provider_factory=stubs)
    assert RF.verify_checksums(out)
    (out / "metrics.md").write_text("changed", encoding="utf-8")
    assert not RF.verify_checksums(out)


def test_pin_writes_the_two_pin_files(repo):
    RF.pin(repo, ollama=OLLAMA_OK)
    assert json.loads((repo / "eval/final_test/model_pin.json").read_text())["model_digest"] == "abc"
    assert json.loads((repo / "eval/final_test/test_data_pin.json").read_text())["sha256"] == RF.test_data_hash(repo, list(GT))


# ------------------------------------------------------------------------------------------------------------ intervals
def test_wilson_matches_known_values():
    lo, hi = wilson(8, 10)
    assert (round(lo, 4), round(hi, 4)) == (0.4902, 0.9433)
    lo, hi = wilson(0, 20)
    assert lo == 0.0 and round(hi, 4) == 0.1611
    assert wilson(20, 20)[1] == 1.0 and wilson(0, 0) is None
    lo, hi = wilson(50, 100)
    assert round(lo, 4) == 0.4038 and round(hi, 4) == 0.5962


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert percentile([0, 10], 0.25) == 2.5


def test_bootstrap_is_seeded_and_brackets_the_estimate():
    docs = [Counter(med_tp=random.Random(i).choice([1, 2, 3]), med_fp=random.Random(i + 99).choice([0, 0, 1]), med_fn=random.Random(i + 7).choice([0, 0, 1])) for i in range(40)]
    f = lambda c: R.summarize(c)["med_f1"]  # noqa: E731
    a = bootstrap_ci(docs, f, n=500, seed=1)
    b = bootstrap_ci(docs, f, n=500, seed=1)
    c = bootstrap_ci(docs, f, n=500, seed=2)
    assert a == b and a != c
    total = Counter()
    for d in docs:
        total += d
    assert a[0] <= f(total) <= a[1]
    assert bootstrap_ci([], f) is None
    # constant data: the interval collapses onto the value
    same = [Counter(med_tp=1) for _ in range(5)]
    assert bootstrap_ci(same, f, n=100, seed=3) == (1.0, 1.0)


def test_extraction_metrics_have_intervals_and_pool_by_document(repo, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for c in RF.CONDS:
        for d in GT:
            out = from_ground_truth(ExtractedDocument.model_validate_json((repo / "data/ground_truth" / f"{d}.json").read_text(encoding="utf-8")))
            (raw_dir / f"{c}_{d}.json").write_text(out.model_dump_json(), encoding="utf-8")
    counters, records, unreadable = R.per_document_counters(repo, raw_dir, set(GT))
    assert len(counters) == 15 and unreadable == []
    m = R.extraction_metrics(counters, "normalised")
    assert m["all"]["med_f1"] == 1.0 and m["all"]["intervals"]["med_precision"][1] == 1.0 and m["all"]["counts"]["documents"] == 3
    fl = R.flag_metrics(records)
    assert fl["all"]["medicines"] == 20 and fl["all"]["wrong_resolved_generic"] == 0
    (raw_dir / "clean_t1.json").write_text("{not json", encoding="utf-8")
    _, _, bad = R.per_document_counters(repo, raw_dir, set(GT))
    assert bad == ["clean_t1"]


def test_safety_block_is_scrubbed_of_pair_level_levels():
    m = R.scrub_safety({"ground_truth": {"pairs": 5, "interactions_by_level": {"major": 1}}, "duplicates": {"flagged": 1, "false_cases": [1], "missed_cases": [2]},
                        "safety": {"silent_misses_strict": 2, "silent_misses_not_covered_by_a_flag": 1, "silent_miss_cases": [{"gt_level": "major"}], "downgrade_cases": [], "false_alarm_cases": [], "level_mismatch_cases": [], "level_mismatches": 0}})
    text = json.dumps(m)
    assert "major" not in text and m["safety"]["silent_misses_covered_by_a_flag"] == 1


# ------------------------------------------------------------------------------------------------------- freeze manifest
def test_freeze_manifest_detects_drift_additions_and_removals(repo):
    assert FM.verify(repo, with_settings=False) == []
    (repo / "backend/app/x.py").write_text("X = 3\n")
    (repo / "backend/app/new.py").write_text("N = 1\n")
    (repo / "eval/final_test/y.py").unlink()
    d = FM.verify(repo, with_settings=False)
    assert "changed: backend/app/x.py" in d and "added: backend/app/new.py" in d and "removed: eval/final_test/y.py" in d


def test_freeze_manifest_excludes_outputs_pins_and_never_hashes_test_documents(repo):
    (repo / "eval/results/final-test-v1").mkdir(parents=True)
    (repo / "eval/results/final-test-v1/metrics.json").write_text("{}")
    m = FM.build(repo, with_settings=False)
    assert not any(k.startswith("eval/results") or "pin" in k for k in m["files"])
    assert not any("ground_truth" in k or "synthetic" in k or "rendered" in k for k in m["files"])
    assert set(m["hash_only"]) == {"dataset_manifest", "ddinter_derived_store"}


def test_the_freeze_script_has_no_path_to_the_test_documents():
    src = (REPO / "scripts" / "freeze_manifest.py").read_text(encoding="utf-8")
    assert "ground_truth" not in src and "data/synthetic" not in src and "data/rendered" not in src


def test_dev_vs_test_table_reads_the_committed_dev_metrics():
    rows = R.dev_vs_test({"extraction": {"raw": {"all": {"med_f1": 0.9}}, "normalised": {"all": {}}}, "flags": {}, "safety": {}, "explanation": {}})
    by = {r["metric"]: r for r in rows}
    assert by["medicine F1, raw"]["dev"] == 0.9833 and by["medicine F1, raw"]["test"] == 0.9 and by["medicine F1, raw"]["diff"] == round(0.9 - 0.9833, 4)
    assert by["silent misses not covered by a flag"]["dev"] == 0 and by["silent misses not covered by a flag"]["test"] is None
    assert len(rows) >= 18
