"""Read-only structure report of the DDInter raw CSVs (counts only)."""
import codecs
import collections
import csv
import glob
import os

pairs = collections.defaultdict(set)
lv = collections.Counter()
tot = 0
for f in sorted(glob.glob("data/reference/ddinter/raw/*.csv")):
    bom = open(f, "rb").read(3) == codecs.BOM_UTF8
    rows = list(csv.DictReader(open(f, encoding="utf-8-sig")))
    print(os.path.basename(f), len(rows), list(rows[0]), "bom", bom)
    tot += len(rows)
    for r in rows:
        lv[r["Level"]] += 1
        a, b = r["Drug_A"].lower(), r["Drug_B"].lower()
        pairs[frozenset((a, b))].add((f[-5], a < b))
print("rows", tot, dict(lv), "distinct pairs", len(pairs))
print("pairs in >1 file", sum(len({x[0] for x in v}) > 1 for v in pairs.values()))
print("pairs seen in both orders", sum(len({x[1] for x in v}) > 1 for v in pairs.values()))
print("example row", rows[0])
