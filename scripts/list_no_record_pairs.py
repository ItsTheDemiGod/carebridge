"""Lists formulary pairs with no record in the DDInter-derived store (candidates for the curated supplement). Counts + a lookup of named pairs."""
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.safety import interactions as I  # noqa: E402
from app.safety.names import formulary_generics  # noqa: E402


def no_record_pairs():
    d = I.load_data()
    return [(a, b) for a, b in combinations(formulary_generics(), 2) if I.check(a, b, d).status == I.NO_RECORD]


if __name__ == "__main__":
    n = no_record_pairs()
    print(len(n), "no-record pairs of 2145")
    if len(sys.argv) > 1:
        want = {frozenset(x.split("+")) for x in sys.argv[1:]}
        for a, b in n:
            if frozenset((a, b)) in want:
                print("NO RECORD:", a, "+", b)
