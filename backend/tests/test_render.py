import hashlib
import json
import sys

import numpy as np
from PIL import Image

from app.services.guards import REPO

sys.path.insert(0, str(REPO / "data"))
import render_documents as rd  # noqa: E402


def test_render_deterministic_and_in_bounds():
    font = rd.load_font()
    text = (REPO / "data/synthetic/ds_003.txt").read_text(encoding="utf-8")
    for cond in rd.CONDITIONS[1:]:  # render() asserts the text stays inside the image
        a, pa = rd.render(text, cond, "ds_003", font)
        b, pb = rd.render(text, cond, "ds_003", font)
        assert a.tobytes() == b.tobytes() and pa == pb
        arr = np.asarray(a)
        assert arr.size and arr.std() > 5  # non-empty, has contrast


def test_rendered_files_complete():
    m = REPO / "data/rendered/manifest.json"
    assert m.exists(), "run data/render_documents.py first"
    entries = json.loads(m.read_text(encoding="utf-8"))["renders"]
    assert len(entries) == 240
    for e in entries:
        for f in e["files"]:
            assert (REPO / "data/rendered" / f).stat().st_size > 1000, f
        assert Image.open(REPO / "data/rendered" / e["files"][0]).size == tuple(e["size"])
    assert sum(e["condition"] in ("clean", "scan") for e in entries) == 120  # these also have PDFs


def test_script_output_identical_across_runs(tmp_path, monkeypatch):
    """Run the renderer twice into temp dirs (first 2 documents) and compare file hashes."""
    hashes = []
    for run in ("a", "b"):
        monkeypatch.setattr(rd, "OUT", tmp_path / run)
        rd.main(limit=2)
        hashes.append({f"{p.parent.name}/{p.name}": hashlib.sha1(p.read_bytes()).hexdigest() for p in (tmp_path / run).rglob("*") if p.suffix in (".png", ".pdf")})
    assert hashes[0] == hashes[1] and len(hashes[0]) == 2 * 6
