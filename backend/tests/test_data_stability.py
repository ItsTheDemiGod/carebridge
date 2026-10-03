"""Phase 2a: name changes must not alter anything else in the dataset (compared with the Phase 1 commit)."""
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PHASE1 = "268e6ea"
FEMALE = {"Asha", "Meena", "Lakshmi", "Fatima", "Anitha", "Deepa", "Priya", "Kavya", "Nasreen", "Sunita"}


def old(path):
    r = subprocess.run(["git", "show", f"{PHASE1}:{path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        pytest.skip("Phase 1 commit not available")
    return r.stdout


def strip_spans(med):
    med = json.loads(json.dumps(med))
    med["source_span"] = med["source_span"]["text"]  # offsets shift when the name length changes
    if med["frequency"]["timing_label"] == "other":
        med["frequency"]["timing_label"] = "unspecified"
    return med


def test_manifest_unchanged():
    assert json.loads(old("data/manifest.json")) == json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))


def test_medications_unchanged():
    for doc in json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))["documents"]:
        p = f"data/ground_truth/{doc['id']}.json"
        new = json.loads((ROOT / p).read_text(encoding="utf-8"))["medications"]
        prev = json.loads(old(p))["medications"]
        assert [strip_spans(m) for m in prev] == [strip_spans(m) for m in new], doc["id"]


def test_name_matches_sex_and_no_other_label():
    for f in (ROOT / "data/synthetic").glob("*.txt"):
        t = f.read_text(encoding="utf-8")
        first, sex = re.search(r"Patient: (\w+) \w+\s+Age/Sex: \d+/([MF])", t).groups()
        assert (first in FEMALE) == (sex == "F"), f.name
        word = re.search(r"-year-old (man|woman),", t)
        assert word is None or (word.group(1) == "woman") == (sex == "F"), f.name
    for f in (ROOT / "data/ground_truth").glob("*.json"):
        assert '"timing_label": "other"' not in f.read_text(encoding="utf-8")
