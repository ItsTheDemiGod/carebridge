"""Aggregate the Phase 3e dev re-run into eval/results/<run-id>/metrics.{json,md}.   python -m eval.phase3e_metrics --run-id phase3e-dev-clean
Needs eval/runs/<run-id>/docs (python -m eval.run_narrative --run-id <run-id>). Compares with eval/results/phase3-dev-clean (Phase 3).
Reports, per language and per kind: share of lines by final provenance, share shown in the language (library + model_checked) versus original-English fallback,
the most frequent near-misses (REPORTING ONLY: never displayed, and never added to the library from dev lines), and library coverage on the stress-set sources.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))
from app.services import phrase_match as pm  # noqa: E402

KINDS = ("advice", "follow_up", "warning")
LANGS = ("en", "ta", "hi")
PROV = ("phrase_library", "model_checked", "original_only")


def pct(a, b):
    return round(a / b, 3) if b else None


def aggregate(run_id: str) -> dict:
    recs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((REPO / "eval" / "runs" / run_id / "docs").glob("*.json"))]
    lines = [(r["doc"], ln) for r in recs for s in r["explanation"]["sections"] for ln in s["lines"] if ln["kind"] in KINDS]
    out = dict(run_id=run_id, documents=len(recs), lines=len(lines), lines_by_kind=dict(Counter(ln["kind"] for _, ln in lines)))
    share = {}
    for lg in LANGS:
        share[lg] = {}
        for k in ("all", *KINDS):
            sel = [ln for _, ln in lines if k == "all" or ln["kind"] == k]
            c = Counter(ln["text"][lg]["provenance"] for ln in sel)
            share[lg][k] = dict(n=len(sel), **{p: pct(c[p], len(sel)) for p in PROV}, shown_in_language=pct(c["phrase_library"] + c["model_checked"], len(sel)),
                                english_fallback=pct(c["original_only"], len(sel)))
    out["provenance_share"] = share
    p3 = REPO / "eval" / "results" / "phase3-dev-clean" / "metrics.json"
    if p3.exists():
        v = json.loads(p3.read_text(encoding="utf-8"))["verified_share"]
        out["phase3_verified_share"] = v
        out["delta_shown_in_language_vs_phase3"] = {lg: {k: (None if v[lg].get(k) is None else round(share[lg][k]["shown_in_language"] - v[lg][k], 3)) for k in ("all", *KINDS)} for lg in LANGS}
    matched = [(d, ln) for d, ln in lines if ln["provenance"] == "phrase_library"]
    out["matched_lines"] = [dict(doc=d, line=ln["line_id"], text=ln["source_text"]) for d, ln in matched]
    # near-misses among lines the library did NOT match (reporting only)
    nm = Counter()
    ratio = {}
    for _, ln in lines:
        if ln["provenance"] == "phrase_library":
            continue
        for x in pm.near_misses(ln["source_text"]):
            key = (pm.normalise(ln["source_text"]), x.phrase_id)
            nm[key] += 1
            ratio[key] = (x.ratio, x.variant)
    out["near_miss_lines"] = len({k[0] for k in nm})
    out["near_misses_top20"] = [dict(line=k[0], phrase=k[1], count=c, ratio=ratio[k][0], closest_wording=ratio[k][1]) for k, c in nm.most_common(20)]
    out["unmatched_line_frequency_top10"] = [dict(line=t, count=c) for t, c in Counter(pm.normalise(ln["source_text"]) for _, ln in lines if ln["provenance"] != "phrase_library").most_common(10)]
    calls = [c for r in recs for c in r["calls"]]
    out["calls"] = dict(total=len(calls), fresh=sum(not c["cached"] for c in calls), failed=sum(bool(c["error"]) for c in calls), total_latency_s=round(sum(c["latency_s"] for c in calls)))
    st = REPO / "eval" / "stress" / "stress_set.json"
    if st.exists():
        s = json.loads(st.read_text(encoding="utf-8"))
        real = [p["source"] for p in s["english_pairs"]] + [i["text"] for i in s["simplify_sources"]]
        short = sorted({p["source"] for lg in ("ta", "hi") for p in s["translation_pairs"][lg]})
        cov = lambda t: dict(lines=len(t), matched=sum(bool(pm.match(x)) for x in t), share=pct(sum(bool(pm.match(x)) for x in t), len(t)))  # noqa: E731
        out["stress_source_coverage"] = dict(realistic_english_sources=cov(real), short_translation_sources=cov(short),
                                              note="The short translation sources were written after the library and are biased towards it; the realistic sources are the second, independent estimate.")
    return out


def markdown(m: dict) -> str:
    L = [f"# {m['run_id']}", "", f"{m['documents']} dev documents (clean condition), {m['lines']} free-text lines {m['lines_by_kind']}. Phrase library active (pipeline: library, model with verification, original English). "
         f"Calls: {m['calls']['total']} ({m['calls']['fresh']} fresh, {m['calls']['failed']} failed), {m['calls']['total_latency_s']} s.", "",
         "**Coverage caveat.** Dev-set coverage is probably optimistic because the synthetic generator's wording is common wording; real-world coverage is unmeasured. The same 8B model writes, back-translates and judges, so `model_checked` means software-checked only, never human-reviewed.", "",
         "## Share of lines by final provenance", "", "| lang | kind | n | phrase_library | model_checked | original_only | shown in language | English fallback |", "|---|---|---|---|---|---|---|---|"]
    for lg in LANGS:
        for k, v in m["provenance_share"][lg].items():
            L.append(f"| {lg} | {k} | {v['n']} | {v['phrase_library']} | {v['model_checked']} | {v['original_only']} | {v['shown_in_language']} | {v['english_fallback']} |")
    if "phase3_verified_share" in m:
        L += ["", "## Comparison with Phase 3 (verified share, no library)", "", "| lang | kind | Phase 3 | Phase 3e shown in language | change |", "|---|---|---|---|---|"]
        for lg in LANGS:
            for k in ("all", *KINDS):
                L.append(f"| {lg} | {k} | {m['phase3_verified_share'][lg][k]} | {m['provenance_share'][lg][k]['shown_in_language']} | {m['delta_shown_in_language_vs_phase3'][lg][k]:+} |")
    L += ["", "## Library matches in the dev set", "", f"{len(m['matched_lines'])} lines: " + "; ".join(f"{x['doc']}/{x['line']}: {x['text']}" for x in m["matched_lines"]), "",
          f"## Near-misses (reporting only, never displayed; {m['near_miss_lines']} unmatched lines have one)", "", "| count | ratio | dev line | closest library wording |", "|---|---|---|---|"]
    L += [f"| {x['count']} | {x['ratio']} | {x['line']} | {x['closest_wording']} ({x['phrase']}) |" for x in m["near_misses_top20"]]
    L += ["", "## Most frequent unmatched lines (top 10)", ""] + [f"- {x['count']}x {x['line']}" for x in m["unmatched_line_frequency_top10"]]
    c = m.get("stress_source_coverage")
    if c:
        L += ["", "## Library coverage on the stress-set sources (second estimate)", "", f"- realistic English sources: {c['realistic_english_sources']['matched']}/{c['realistic_english_sources']['lines']} ({c['realistic_english_sources']['share']})",
              f"- short translation sources: {c['short_translation_sources']['matched']}/{c['short_translation_sources']['lines']} ({c['short_translation_sources']['share']}); {c['note']}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="phase3e-dev-clean")
    a = ap.parse_args()
    m = aggregate(a.run_id)
    d = REPO / "eval" / "results" / a.run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    (d / "metrics.md").write_text(markdown(m), encoding="utf-8", newline="\n")
    print(markdown(m)[:3500])
