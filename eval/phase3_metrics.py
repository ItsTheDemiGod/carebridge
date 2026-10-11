"""Aggregate a Phase 3 dev run into eval/results/<run-id>/metrics.{json,md}.   python -m eval.phase3_metrics --run-id phase3-dev-clean
Needs eval/runs/<run-id>/docs (eval.run_narrative); merges corruptions.json (eval.corruption_eval) when present."""

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from eval import readability  # noqa: E402

KINDS = ("advice", "follow_up", "warning")
LANGS = ("en", "ta", "hi")


def reason_type(v: dict) -> str:
    r = v.get("reason") or ""
    return "judge:" + (v.get("judge_verdict") or "none") if r.startswith("judge:") else r.split(":")[0] or "none"


def load(run_id):
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted((REPO / "eval" / "runs" / run_id / "docs").glob("*.json"))]


def pct(a, b):
    return round(a / b, 3) if b else None


def aggregate(run_id: str) -> dict:
    recs = load(run_id)
    lines = [(r["doc"], ln) for r in recs for s in r["explanation"]["sections"] for ln in s["lines"] if ln["kind"] in KINDS]
    out = dict(run_id=run_id, documents=len(recs), lines=len(lines), lines_by_kind=dict(Counter(ln["kind"] for _, ln in lines)),
               medicine_lines=sum(1 for r in recs for s in r["explanation"]["sections"] for ln in s["lines"] if ln["kind"] == "medicine"))
    out["verified_share"] = {lg: {"all": pct(sum(ln["text"][lg]["status"] == "verified" for _, ln in lines), len(lines)),
                                  **{k: pct(sum(ln["text"][lg]["status"] == "verified" for _, ln in lines if ln["kind"] == k), sum(ln["kind"] == k for _, ln in lines)) for k in KINDS}} for lg in LANGS}
    out["line_verified_all_languages"] = pct(sum(ln["status"] == "verified" for _, ln in lines), len(lines))
    out["fallback_rate"] = {lg: pct(sum(ln["text"][lg]["display_mode"] == "original_with_notice" for _, ln in lines), len(lines)) for lg in LANGS}
    out["failure_reasons"] = {lg: dict(Counter(reason_type(ln["text"][lg]["verification"]) for _, ln in lines if ln["text"][lg]["status"] != "verified").most_common()) for lg in LANGS}
    det = {lg: Counter() for lg in LANGS}
    for _, ln in lines:
        for lg in LANGS:
            det[lg].update(k for k, ok in ln["text"][lg]["verification"]["deterministic"].items() if not ok)
    out["deterministic_check_failures_any"] = {lg: dict(c) for lg, c in det.items()}
    out["judge_verdicts"] = {lg: dict(Counter(ln["text"][lg]["verification"]["judge_verdict"] for _, ln in lines)) for lg in LANGS}
    lat = defaultdict(list)
    calls = [c for r in recs for c in r["calls"]]
    for c in calls:
        lat[c["stage"]].append(c["latency_s"])
    out["latency_s_by_call_type"] = {k: dict(n=len(v), median=round(statistics.median(v), 1), p95=round(sorted(v)[int(0.95 * (len(v) - 1))], 1), max=round(max(v), 1)) for k, v in lat.items()}
    out["calls"] = dict(total=len(calls), failed=sum(bool(c["error"]) for c in calls), errors=dict(Counter(c["error"] for c in calls if c["error"])), total_latency_s=round(sum(c["latency_s"] for c in calls)),
                        tokens=sum(c["usage"].get("total_tokens", 0) for c in calls))
    src = [ln["source_text"] for _, ln in lines]
    plain = [ln["text"]["en"]["verification"]["candidate"] for _, ln in lines if ln["text"]["en"]["verification"]["candidate"]]
    plain_ok = [ln["text"]["en"]["text"] for _, ln in lines if ln["text"]["en"]["status"] == "verified"]
    out["readability"] = dict(source=readability.summarize(src), plain_english_all=readability.summarize(plain), plain_english_verified=readability.summarize(plain_ok),
                              note="English only; Tamil and Hindi readability is not scored.")
    cj = REPO / "eval" / "results" / run_id / "corruptions.json"
    out["corruptions"] = json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else None
    return out


def markdown(m: dict) -> str:
    L = [f"# {m['run_id']}", "", f"{m['documents']} dev documents (clean condition), {m['lines']} free-text lines {m['lines_by_kind']}, {m['medicine_lines']} template medicine lines. Calls: {m['calls']['total']} ({m['calls']['failed']} failed). "
         "The same local 8B model writes and judges, which weakens the judge; native review in Phase 7 is the real check on Tamil and Hindi.", "",
         "## Verified share (a language text is verified only if all deterministic checks pass AND the judge says supported)", "", "| lang | all | advice | follow_up | warning | fallback rate |", "|---|---|---|---|---|---|"]
    L += [f"| {lg} | {v['all']} | {v['advice']} | {v['follow_up']} | {v['warning']} | {m['fallback_rate'][lg]} |" for lg, v in m["verified_share"].items()]
    L += ["", f"Lines verified in all three languages: {m['line_verified_all_languages']}", "", "## Failure reasons (first failing check or judge verdict)", ""]
    L += [f"- {lg}: {m['failure_reasons'][lg]}" for lg in LANGS]
    L += ["", "Deterministic checks failed (any, not only first): " + str(m["deterministic_check_failures_any"]), "", "Judge verdicts: " + str(m["judge_verdicts"]), "", "## Latency per call type (s)", "", "| type | n | median | p95 | max |", "|---|---|---|---|---|"]
    L += [f"| {k} | {v['n']} | {v['median']} | {v['p95']} | {v['max']} |" for k, v in m["latency_s_by_call_type"].items()]
    L += ["", f"Total model time {m['calls']['total_latency_s']} s, {m['calls']['tokens']} tokens.", "", "## English readability (Flesch-Kincaid grade; heuristic, see eval/readability.py)", "", "| set | lines | FK median | p25-p75 | pooled FK | mean sentence len | share words > 12 letters |", "|---|---|---|---|---|---|---|"]
    for k, v in m["readability"].items():
        if isinstance(v, dict):
            L.append(f"| {k} | {v['lines']} | {v['fk_median']} | {v['fk_p25']} to {v['fk_p75']} | {v['pooled_fk_grade']} | {v['mean_sentence_len']} | {v['long_word_share']} |")
    c = m["corruptions"]
    if c:
        L += ["", "## Corruption detection (known faults; deterministic alone / judge alone / combined)", "",
              "Tamil/Hindi cover only number_changed, drug_name_swapped, wrong_script, item_dropped. Negation and urgency changes in Tamil/Hindi cannot be generated or checked deterministically and are NOT measured.", "",
              "| lang/type | n | deterministic | judge | combined |", "|---|---|---|---|---|"]
        L += [f"| {k} | {v['n']} | {v['deterministic']} | {v['judge']} | {v['combined']} |" for k, v in c["by_type"].items()]
        d = c["item_dropped"]
        L += [f"| item_dropped (batch) | {d['n']} | {d['deterministic']} | n/a | {d['combined']} |", "", f"False-reject rate on uncorrupted lines (source line as candidate): {c['false_reject_identity']}", f"Model plain English rejected: {c['model_plain_english_reject_rate']}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="phase3-dev-clean")
    a = ap.parse_args()
    m = aggregate(a.run_id)
    d = REPO / "eval" / "results" / a.run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    (d / "metrics.md").write_text(markdown(m), encoding="utf-8", newline="\n")
    print(markdown(m)[:2500])
