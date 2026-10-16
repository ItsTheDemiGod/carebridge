"""Empirical check of the coverage rule (Step 2c). Reads only the DDInter raw files and data/reference/formulary_atc.json. Counts only.
Run from the repo root: python scripts/evidence/validate_coverage_rule.py"""
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coverage as C  # noqa: E402

RANK = {"Major": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}


def main():
    rows = C.read_raw()
    ap = C.appears_in(rows)
    best, seen = {}, set()
    for _, a, b, lv in rows:
        k = frozenset((a, b))
        seen.add(k)
        if RANK[lv] >= RANK.get(best.get(k), -1):
            best[k] = lv
    atc = C.load_atc()
    comps = {g: [(c["ddinter_name"].lower(), c["atc_codes"]) for c in e["components"]] for g, e in atc.items()}
    uv = sorted({n for cs in comps.values() for n, codes in cs if C.unverified(n, codes, ap)})
    print("coverage_unverified components:", uv)
    # component level (distinct component pairs)
    cp = {}
    for a, b in combinations(sorted({c[0]: c for cs in comps.values() for c in cs}.values(), key=lambda c: c[0]), 2):
        if a[0] != b[0]:
            cp[(a[0], b[0])] = C.covered(a, b, ap)
    bad = [k for k, v in cp.items() if not v and frozenset(k) in seen]
    print(f"component pairs {len(cp)}: covered {sum(cp.values())}, not covered {len(cp) - sum(cp.values())}; NOT covered yet in a downloaded file: {len(bad)}")
    if bad:
        print("VIOLATIONS:", bad[:20])
        sys.exit(1)
    # formulary-pair level
    cls, lev = Counter(), Counter()
    for a, b in combinations(atc, 2):
        pairs = [(x, y) for x in comps[a] for y in comps[b] if x[0] != y[0]]
        allcov = bool(pairs) and all(C.covered(x, y, ap) for x, y in pairs)
        found = [best[frozenset((x[0], y[0]))] for x, y in pairs if frozenset((x[0], y[0])) in best]
        if found:
            lv = max(found, key=RANK.get)
            cls["covered_with_interaction" if allcov else "partly_covered_with_interaction"] += 1
            lev[("covered" if allcov else "partly covered", lv)] += 1
        else:
            cls["covered_no_listing" if allcov else "not_covered"] += 1
    print("formulary pairs (2,145):", dict(cls))
    print("interactions by level:", {k: v for k, v in sorted(lev.items(), key=str) if isinstance(k, tuple)})


if __name__ == "__main__":
    main()
