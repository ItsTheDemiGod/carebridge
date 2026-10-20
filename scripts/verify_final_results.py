"""Independent check of eval/results/final-test-v1 (read-only, standard library only).

Recomputes the extraction headline numbers from per_document.csv and checks the flag/safety numbers in metrics.json for internal consistency
(they cannot be recomputed from the CSV, which carries only the medicine counters). Writes nothing. Exit 1 on any difference.
"""
import csv, json, math, random, sys
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "eval/results/final-test-v1"
CONDS = ["text", "clean", "scan", "photo", "poor"]
SEED, NB, Z = 20261018, 2000, 1.959963984540054
bad: list[str] = []


def wilson(k, n):
    if n <= 0:
        return None
    p, d = k / n, 1 + Z * Z / n
    c, h = (p + Z * Z / (2 * n)) / d, Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def f1(c):
    p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0
    r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0
    return 2 * p * r / (p + r) if p + r else 0


def fully(c):
    return c["fc"] / c["tp"] if c["tp"] else None


def boot(docs, stat):
    rng, vals = random.Random(SEED), []
    for _ in range(NB):
        t = Counter()
        for _ in docs:
            t += docs[rng.randrange(len(docs))]
        v = stat(t)
        if v is not None:
            vals.append(v)
    vals.sort()

    def pct(q):
        pos = q * (len(vals) - 1)
        lo, hi = math.floor(pos), math.ceil(pos)
        return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)
    return [round(pct(0.025), 4), round(pct(0.975), 4)]


def chk(label, mine, theirs, tol=1.01e-4):  # 3 bootstrap bounds differ by 0.0001: eval/matching.py computes F1 from precision and recall already rounded to 4 decimals
    ok = (mine == theirs) if not isinstance(mine, float) else abs(mine - theirs) <= tol
    if isinstance(mine, list):
        ok = all(abs(a - b) <= tol for a, b in zip(mine, theirs)) and len(mine) == len(theirs)
    if not ok:
        bad.append(f"{label}: recomputed {mine} vs metrics.json {theirs}")


rows = list(csv.DictReader((D / "per_document.csv").open(encoding="utf-8")))
m = json.loads((D / "metrics.json").read_text(encoding="utf-8"))
for variant in ("raw", "normalised"):
    for cond in (*CONDS, "all"):
        by_doc = defaultdict(Counter)
        for r in rows:
            if r["variant"] == variant and (cond == "all" or r["condition"] == cond):
                by_doc[r["document"]] += Counter(tp=int(r["med_tp"]), fp=int(r["med_fp"]), fn=int(r["med_fn"]), fc=int(r["med_fully_correct"]), inv=int(r["invented"]), nul=int(r["null_total"]))
        docs = [by_doc[d] for d in sorted(by_doc)]
        c = sum(docs, Counter())
        s, iv, ct = m["extraction"][variant][cond], m["extraction"][variant][cond]["intervals"], m["extraction"][variant][cond]["counts"]
        t = f"{variant}/{cond}"
        chk(t + " documents", len(docs), ct["documents"])  # s["docs"] is condition-documents when pooled (200)
        chk(t + " precision", round(c["tp"] / (c["tp"] + c["fp"]), 4), s["med_precision"])
        chk(t + " recall", round(c["tp"] / (c["tp"] + c["fn"]), 4), s["med_recall"])
        chk(t + " F1", round(f1(c), 4), s["med_f1"])
        chk(t + " fully-correct", round(c["fc"] / c["tp"], 4), s["med_fully_correct_rate"])
        chk(t + " hallucinated", c["fp"], s["hallucinated_meds"])
        chk(t + " invented rate", round(c["inv"] / c["nul"], 4), s["invented_value_rate"])
        chk(t + " counts", [c["tp"], c["fp"], c["fn"], c["fc"], c["inv"], c["nul"]], [ct[k] for k in ("med_tp", "med_fp", "med_fn", "med_fully_correct", "invented", "null_total")])
        chk(t + " precision CI", wilson(c["tp"], c["tp"] + c["fp"]), iv["med_precision"])
        chk(t + " recall CI", wilson(c["tp"], c["tp"] + c["fn"]), iv["med_recall"])
        chk(t + " fully CI (Wilson)", wilson(c["fc"], c["tp"]), iv["med_fully_correct_rate"])
        chk(t + " invented CI", wilson(c["inv"], c["nul"]), iv["invented_value_rate"])
        chk(t + " F1 bootstrap", boot(docs, f1), iv["med_f1_bootstrap"])
        chk(t + " fully bootstrap", boot(docs, fully), iv["med_fully_correct_rate_bootstrap"])
        if cond == "all":
            print(f"{variant:10} pooled: F1 {s['med_f1']} fully {s['med_fully_correct_rate']} halluc {s['hallucinated_meds']} (from {len(rows)//2} condition-documents)")

# flags: pooled == sum of conditions, shares == k/n, Wilson intervals, attempted == scored + skipped
fl = m["flags"]
for k in ("medicines", "must_confirm", "name_errors_remaining", "name_errors_unflagged", "timing_errors_remaining", "timing_errors_unflagged", "interaction_ready", "schedule_ready", "wrong_resolved_generic", "wrong_schedule"):
    chk("flags pooled " + k, sum(fl[c][k] for c in CONDS), fl["all"][k])
for c in (*CONDS, "all"):
    chk(f"flags {c} share_must_confirm", round(fl[c]["must_confirm"] / fl[c]["medicines"], 4), fl[c]["share_must_confirm"])
    chk(f"flags {c} must_confirm CI", wilson(fl[c]["must_confirm"], fl[c]["medicines"]), fl[c]["share_must_confirm_ci"])
    chk(f"flags {c} wrong_schedule CI", wilson(fl[c]["wrong_schedule"], fl[c]["schedule_ready"]), fl[c]["wrong_schedule_ci"])
    chk(f"flags {c} wrong_resolved CI", wilson(fl[c]["wrong_resolved_generic"], fl[c]["interaction_ready"]), fl[c]["wrong_resolved_generic_ci"])
    o = m["operational"][c]
    chk(f"operational {c} attempted = scored + skipped", o["attempted"], o["scored"] + o["skipped"])
sf = m["safety"]["safety"]
chk("silent misses strict = covered + not covered", sf["silent_misses_strict"], sf["silent_misses_covered_by_a_flag"] + sf["silent_misses_not_covered_by_a_flag"])
print("wrong resolved_generic among interaction_ready:", fl["all"]["wrong_resolved_generic"], "| wrong schedule among schedule_ready:", fl["all"]["wrong_schedule"])
print("differences:", len(bad))
for b in bad:
    print(" ", b)
sys.exit(1 if bad else 0)
