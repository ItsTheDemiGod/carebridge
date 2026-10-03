import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data"))
from validate_dataset import validate  # noqa: E402


def test_dataset_valid():
    errors, _ = validate()
    assert errors == []
