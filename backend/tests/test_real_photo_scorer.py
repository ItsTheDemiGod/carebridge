"""Phase 7a: the real-photo scorer (scripts/score_real_photos.py) driven through the REAL app path with a mocked provider and fixture photos. No model, no real photos."""
import json
import sys

import pytest
from PIL import Image

from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import from_ground_truth
from app.services.guards import REPO
from tests.apihelpers import Env, FakeOllama
from tests.test_final_harness import GT, gt_json

sys.path.insert(0, str(REPO / "scripts"))
import score_real_photos as S  # noqa: E402


def fixture(tmp, photos=("RP1_A.jpg", "RP1_B.jpg", "RP1_C.jpg")):
    root = tmp / "root"
    (root / "data/real_photos").mkdir(parents=True)
    (root / "data/synthetic").mkdir(parents=True)
    (root / "data/ground_truth").mkdir(parents=True)
    (root / "data/synthetic/t2.txt").write_text("Tab Telma 40 mg 1 tablet once daily\nTab Lipitor 10 mg 1 tablet at bedtime\n", encoding="utf-8")
    (root / "data/ground_truth/t2.json").write_text(json.dumps(gt_json(GT["t2"])), encoding="utf-8")
    folder = root / "data/real_photos"
    (folder / "mapping.json").write_text(json.dumps({"RP1": {"source": "dev", "id": "t2", "text": "data/synthetic/t2.txt", "ground_truth": "data/ground_truth/t2.json", "category": "fixture"}}), encoding="utf-8")
    for i, n in enumerate(photos):
        Image.new("RGB", (40 + i, 30), (200, 200, 200)).save(folder / n, "JPEG")
    return root, folder


def gt_output():
    return from_ground_truth(ExtractedDocument.model_validate_json(json.dumps(gt_json(GT["t2"]))))


def test_scores_photos_through_the_api_and_aggregates_per_condition(tmp_path):
    root, folder = fixture(tmp_path)
    with Env(tmp_path) as env:
        env.provider = FakeOllama(gt_output())
        m = S.run(env.client, folder, root=root, out_dir=tmp_path / "out", sleep=0.05)
        assert env.provider.calls and len(env.provider.calls) == 3
    assert m["photos_found"] == 3 and m["skipped"] == []
    a = m["by_condition"]["all"]
    assert a["photos_scored"] == 3 and a["med_f1"] == 1.0 and a["medicines"] == 6 and a["intervals"]["med_precision"][1] == 1.0
    assert set(m["by_condition"]) == {"A", "B", "C", "all"}
    assert (tmp_path / "out/metrics.json").exists() and "Wilson" in (tmp_path / "out/metrics.md").read_text(encoding="utf-8")
    assert "real photos (pooled)" in (tmp_path / "out/comparison.md").read_text(encoding="utf-8")
    assert len(m["comparison_with_dev_rendered"]) == 3 and m["comparison_with_dev_rendered"][0]["dev rendered poor"] is not None


def test_sessions_are_deleted_after_each_photo(tmp_path):
    root, folder = fixture(tmp_path, ("RP1_A.jpg",))
    with Env(tmp_path) as env:
        env.provider = FakeOllama(gt_output())
        S.run(env.client, folder, root=root, sleep=0.05)
        with env.ctx.db.session() as c:
            assert c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
            assert c.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0


def test_refuses_files_that_are_not_in_the_mapping_and_uploads_nothing(tmp_path):
    root, folder = fixture(tmp_path)
    (folder / "RP9_A.jpg").write_bytes(b"x")
    (folder / "holiday.jpg").write_bytes(b"x")
    with Env(tmp_path) as env:
        env.provider = FakeOllama(gt_output())
        with pytest.raises(S.Refusal, match="2 file"):
            S.run(env.client, folder, root=root, sleep=0.05)
        assert env.provider.calls == []


def test_failed_uploads_are_listed_not_dropped(tmp_path):
    root, folder = fixture(tmp_path, ("RP1_A.jpg", "RP1_B.jpg"))
    with Env(tmp_path) as env:
        env.provider = FakeOllama(error="context_truncated")
        m = S.run(env.client, folder, root=root, sleep=0.05)
    assert len(m["skipped"]) == 2 and m["skipped"][0]["reason"].startswith("failed_")
    assert m["by_condition"] == {}


def test_output_has_only_aggregates_and_ids(tmp_path):
    root, folder = fixture(tmp_path, ("RP1_D.jpg",))
    with Env(tmp_path) as env:
        env.provider = FakeOllama(gt_output())
        S.run(env.client, folder, root=root, out_dir=tmp_path / "o", sleep=0.05)
    text = (tmp_path / "o/metrics.json").read_text(encoding="utf-8")
    for leak in ("Telma", "Lipitor", "Glycomet", "Sample City", ".jpg"):
        assert leak not in text
