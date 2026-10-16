"""ARCHIVED EVIDENCE, not used by the app (see docs/DDINTER_COVERAGE.md addendum). Which drug pairs the downloaded DDInter files can speak about (docs/SAFETY.md).

RULE: a component pair (X, Y) is COVERED only if at least one of X, Y has an authored ATC letter in DOWNLOADED AND that drug really
appears (either column) in the downloaded file for that letter. A drug authored as a downloaded group that is absent from its file is
"coverage_unverified" and counts as NOT qualifying (conservative). Anything else is NOT covered, so absence is never read as "no interaction".
"""
import csv
import json
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

DOWNLOADED = frozenset("ABDHLPRV")
ATC_FILE = Path(__file__).resolve().parent / "formulary_atc.json"
RAW_DIR = REPO / "data" / "reference" / "ddinter" / "raw"


@lru_cache
def load_atc(path: Path = ATC_FILE) -> dict[str, dict]:
    """generic_name -> entry {atc_codes, components[{ddinter_name, atc_codes}], combination}."""
    return {m["generic_name"]: m for m in json.loads(path.read_text(encoding="utf-8"))["medicines"]}


def read_raw(raw_dir: Path = RAW_DIR) -> list[tuple[str, str, str, str]]:
    """(letter, drug_a, drug_b, level) with names lowercased; letter from the file name ddinter_downloads_code_<L>.csv."""
    rows = []
    for f in sorted(Path(raw_dir).glob("ddinter_downloads_code_*.csv")):
        letter = f.stem[-1].upper()
        with f.open(encoding="utf-8-sig", newline="") as fh:
            rows += [(letter, r["Drug_A"].strip().lower(), r["Drug_B"].strip().lower(), r["Level"].strip()) for r in csv.DictReader(fh)]
    return rows


def appears_in(rows) -> dict[str, list[str]]:
    """lowercased DDInter name -> sorted letters of the files it appears in (either column)."""
    out: dict[str, set[str]] = {}
    for letter, a, b, _ in rows:
        out.setdefault(a, set()).add(letter)
        out.setdefault(b, set()).add(letter)
    return {k: sorted(v) for k, v in out.items()}


def qualifies(name: str, atc_codes: list[str], appears: dict[str, list[str]]) -> bool:
    """True if one of the drug's authored ATC letters is a downloaded group AND the drug is in that letter's file."""
    files = set(appears.get(name.lower(), ()))
    return any(c[0] in DOWNLOADED and c[0] in files for c in atc_codes)


def unverified(name: str, atc_codes: list[str], appears: dict[str, list[str]]) -> bool:
    """Authored as a downloaded group but absent from the matching file(s) (also true when absent from every file)."""
    return any(c[0] in DOWNLOADED for c in atc_codes) and not qualifies(name, atc_codes, appears)


def covered(a: tuple[str, list[str]], b: tuple[str, list[str]], appears: dict[str, list[str]]) -> bool:
    return qualifies(*a, appears) or qualifies(*b, appears)
