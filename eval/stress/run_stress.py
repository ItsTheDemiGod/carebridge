"""Stress evaluation of the verification stack and the English simplifier on authored (blind) test data.

  python -m eval.stress.run_stress --run-id stress-v1 [--only en|ta|hi|simplify]
Local Ollama only (text, localhost); resumable from the narrative disk cache (data/cache/narrative). No document, no dev data, no Gemini.
Per call type the items are sent in chunks (judge 10 English / 6 Tamil-Hindi, back-translation 4 Tamil / 6 Hindi, simplify 8) so one call stays inside the context.
Writes eval/results/<run-id>/metrics.{json,md} (committed) and eval/runs/<run-id>/raw.json (gitignored).

Verified = every deterministic check passes AND the judge says "supported" (the same rule as the product).
FALSE-REJECT = a correct candidate that is not verified. DETECTION = a wrong candidate that is not verified, counted for the deterministic
checks alone, the judge alone, and both combined. Tamil/Hindi: back-translate (Prompt C), then judge(source, back-translation) (Prompt D).
"""

import argparse
import json
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from app.llm.ollama import OllamaProvider  # noqa: E402
from app.services import narrative as nv  # noqa: E402
from app.services import phrase_match as pm  # noqa: E402
from app.services.verification import _stage_value, deterministic  # noqa: E402
from eval import readability  # noqa: E402

STRESS = REPO / "eval" / "stress" / "stress_set.json"
CHUNK = {"judge_en": 10, "judge_ta": 6, "judge_hi": 6, "back_ta": 4, "back_hi": 6, "simplify": 8}
GROUP = {"negation_flipped": "negation_dropped_or_flipped", "negation_dropped": "negation_dropped_or_flipped"}


def chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def run_chunked(fn, data: dict, size: int, label: str, calls: list, *a):
    """Apply a batch function chunk by chunk. Returns (id -> value, id -> problem). A batch problem fails every id of its chunk."""
    values, problems = {}, {}
    for ids in chunks(list(data), size):
        t = time.perf_counter()
        st = fn({i: data[i] for i in ids}, *a)
        calls.append(dict(type=label, items=len(ids), cached=st.call.cached, latency_s=round(st.call.latency_s, 2), api_calls=st.call.api_calls, error=st.call.error, wall_s=round(time.perf_counter() - t, 1)))
        print(f"  {label}: {len(ids)} items, {'cached' if st.call.cached else str(round(st.call.latency_s)) + 's'}{' ERROR ' + st.call.error if st.call.error else ''}", flush=True)
        for i in ids:
            v, p = _stage_value(st, i)
            if v is None:
                problems[i] = p or "no_value"
            else:
                values[i] = v
    return values, problems


def evaluate_pairs(pairs: list[dict], lang: str, provider, calls: list) -> list[dict]:
    """English: judge(source, candidate). Tamil/Hindi: back-translate the candidate, then judge(source, back-translation)."""
    back = {}
    if lang != "en":
        bt, bprob = run_chunked(lambda d, *_: nv.back_translate(d, lang, provider), {p["id"]: p["candidate"] for p in pairs}, CHUNK[f"back_{lang}"], f"back_{lang}", calls)
        back = bt
        back_problem = bprob
    view = {p["id"]: (p["candidate"] if lang == "en" else back.get(p["id"])) for p in pairs}
    to_judge = {p["id"]: (p["source"], view[p["id"]]) for p in pairs if view[p["id"]]}
    jv, jprob = run_chunked(lambda d, *_: nv.judge(d, lang, provider), to_judge, CHUNK[f"judge_{lang}"], f"judge_{lang}", calls)
    out = []
    for p in pairs:
        i = p["id"]
        det, why = deterministic(p["kind"], p["source"], p["candidate"], lang, number_ref=p["source"], english_view=view[i])
        if lang != "en" and view[i] is None:
            det["id_integrity"], why = False, [f"id_integrity: back-translation {back_problem.get(i)}"] + why
        verdict, reason = jv.get(i, (None, jprob.get(i, "judge_unavailable")))
        det_fail = bool(why)
        judge_fail = verdict != "supported"
        out.append(dict(id=i, label=p["label"], wrong_type=GROUP.get(p["wrong_type"], p["wrong_type"]), kind=p["kind"], deterministic=det, det_reasons=why, back_translation=back.get(i),
                        verdict=verdict, judge_reason=reason, judge_unavailable=verdict is None, det_flag=det_fail, judge_flag=judge_fail, verified=not det_fail and not judge_fail))
    return out


def rate(a: int, b: int):
    return round(a / b, 3) if b else None


def summarize_pairs(rows: list[dict]) -> dict:
    ok, bad = [r for r in rows if r["label"] == "correct"], [r for r in rows if r["label"] == "wrong"]
    by_type = defaultdict(list)
    for r in bad:
        by_type[r["wrong_type"]].append(r)
    det_fr = Counter(k for r in ok for k, v in r["deterministic"].items() if not v)
    return dict(
        n=len(rows), correct=len(ok), wrong=len(bad),
        false_reject=dict(rate=rate(sum(not r["verified"] for r in ok), len(ok)), n=sum(not r["verified"] for r in ok), of=len(ok),
                          by_deterministic=sum(r["det_flag"] for r in ok), by_judge=sum(r["judge_flag"] for r in ok), deterministic_checks=dict(det_fr)),
        detection=dict(overall=dict(n=len(bad), deterministic=rate(sum(r["det_flag"] for r in bad), len(bad)), judge=rate(sum(r["judge_flag"] for r in bad), len(bad)), combined=rate(sum(not r["verified"] for r in bad), len(bad))),
                       by_type={t: dict(n=len(v), deterministic=rate(sum(r["det_flag"] for r in v), len(v)), judge=rate(sum(r["judge_flag"] for r in v), len(v)), combined=rate(sum(not r["verified"] for r in v), len(v))) for t, v in sorted(by_type.items())}),
        accuracy=rate(sum(r["verified"] for r in ok) + sum(not r["verified"] for r in bad), len(rows)),
        confusion=dict(correct=dict(verified=sum(r["verified"] for r in ok), rejected=sum(not r["verified"] for r in ok)), wrong=dict(verified=sum(r["verified"] for r in bad), rejected=sum(not r["verified"] for r in bad))),
        judge_unavailable=sum(r["judge_unavailable"] for r in rows),
        false_rejects=[dict(id=r["id"], det=r["det_reasons"], verdict=r["verdict"], reason=r["judge_reason"]) for r in ok if not r["verified"]],
        missed=[dict(id=r["id"], type=r["wrong_type"], verdict=r["verdict"], reason=r["judge_reason"]) for r in bad if r["verified"]])


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower().rstrip(".!"))


def evaluate_simplifier(items: list[dict], provider, calls: list) -> dict:
    src = {i["id"]: i["text"] for i in items}
    kinds = {i["id"]: i["kind"] for i in items}
    plain, prob = run_chunked(lambda d, *_: nv.simplify([nv.Item(id=k, kind=kinds[k], text=t) for k, t in d.items()], provider), src, CHUNK["simplify"], "simplify", calls)
    judged, jprob = run_chunked(lambda d, *_: nv.judge(d, "en", provider), {i: (src[i], plain[i]) for i in plain}, CHUNK["judge_en"], "judge_en(simplify)", calls)
    rows = []
    for i in src:
        p = plain.get(i)
        if p is None:
            rows.append(dict(id=i, plain=None, problem=prob.get(i), unchanged=False, verified=False, lost_or_added=None))
            continue
        det, why = deterministic(kinds[i], src[i], p, "en")
        verdict, reason = judged.get(i, (None, jprob.get(i)))
        rows.append(dict(id=i, source=src[i], plain=p, unchanged=norm(p) == norm(src[i]), det_reasons=why, verdict=verdict, judge_reason=reason, verified=not why and verdict == "supported",
                         lost_or_added=bool(why) or verdict in ("adds_information", "omits_information", "contradicts")))
    ok = [r for r in rows if r["plain"]]
    before, after = readability.summarize([r["source"] for r in ok]), readability.summarize([r["plain"] for r in ok])
    return dict(n=len(rows), produced=len(ok), unchanged_share=rate(sum(r["unchanged"] for r in ok), len(ok)), verified_share=rate(sum(r["verified"] for r in rows), len(rows)),
                fk_before=dict(median=before["fk_median"], pooled=before["pooled_fk_grade"], mean_sentence_len=before["mean_sentence_len"], long_word_share=before["long_word_share"]),
                fk_after=dict(median=after["fk_median"], pooled=after["pooled_fk_grade"], mean_sentence_len=after["mean_sentence_len"], long_word_share=after["long_word_share"]),
                lost_or_added=[dict(id=r["id"], det=r["det_reasons"], verdict=r["verdict"], reason=r["judge_reason"], source=r["source"], plain=r["plain"]) for r in rows if r.get("lost_or_added")],
                rows=rows)


def coverage(texts: list[str]) -> dict:
    hit = [t for t in texts if pm.match(t)]
    return dict(lines=len(texts), matched=len(hit), share=rate(len(hit), len(texts)), matched_lines=hit)


def markdown(m: dict) -> str:
    L = [f"# {m['run_id']}", "", "Authored (blind) stress set; never shipped to users. Local model `" + m["model"] + "`, text only. The same 8B model back-translates and judges, so the judge is weak evidence. "
         "Tamil/Hindi candidates were written by Claude Code and are NOT native-checked: they test whether the judge catches obvious faults and accepts clearly correct text, not translation quality. "
         "Small samples (6 correct and 6 wrong per Tamil/Hindi, 20 and 20 English): read the rates as rough.", ""]
    for lg, name in (("en", "English"), ("ta", "Tamil (back-translation + judge)"), ("hi", "Hindi (back-translation + judge)")):
        s = m.get(lg)
        if not s:
            continue
        fr, d = s["false_reject"], s["detection"]
        L += [f"## {name}", "", f"{s['correct']} correct + {s['wrong']} wrong candidates. **False-reject rate {fr['rate']}** ({fr['n']}/{fr['of']}; deterministic {fr['by_deterministic']}, judge {fr['by_judge']}; failing checks {fr['deterministic_checks']}). "
              f"Overall accuracy {s['accuracy']}. Judge unavailable: {s['judge_unavailable']}.", "", "| wrong type | n | deterministic | judge | combined |", "|---|---|---|---|---|"]
        L += [f"| {t} | {v['n']} | {v['deterministic']} | {v['judge']} | {v['combined']} |" for t, v in d["by_type"].items()]
        o = d["overall"]
        L += [f"| **all wrong** | {o['n']} | {o['deterministic']} | {o['judge']} | {o['combined']} |", "", "Confusion (rows = truth, columns = system verdict):", "", "| truth | verified | rejected |", "|---|---|---|",
              f"| correct | {s['confusion']['correct']['verified']} | {s['confusion']['correct']['rejected']} |", f"| wrong | {s['confusion']['wrong']['verified']} | {s['confusion']['wrong']['rejected']} |", ""]
        if s["missed"]:
            L.append("Missed (wrong but verified): " + "; ".join(f"{x['id']} ({x['type']})" for x in s["missed"]))
        if s["false_rejects"]:
            L.append("False rejects: " + "; ".join(f"{x['id']} ({x['verdict'] or 'det'})" for x in s["false_rejects"]))
        L.append("")
    sm = m.get("simplifier")
    if sm:
        L += ["## English simplifier on harder lines (Prompt A, no reference answer)", "", f"{sm['produced']}/{sm['n']} lines produced. Unchanged: {sm['unchanged_share']}. Verified (deterministic + judge): {sm['verified_share']}.", "",
              "| | FK median | FK pooled | mean sentence length | long-word share |", "|---|---|---|---|---|",
              f"| source | {sm['fk_before']['median']} | {sm['fk_before']['pooled']} | {sm['fk_before']['mean_sentence_len']} | {sm['fk_before']['long_word_share']} |",
              f"| simplified | {sm['fk_after']['median']} | {sm['fk_after']['pooled']} | {sm['fk_after']['mean_sentence_len']} | {sm['fk_after']['long_word_share']} |", ""]
        L.append(f"Lines where a fact appears lost or added (deterministic or judge): {len(sm['lost_or_added'])}")
        L += [f"- {x['id']}: judge {x['verdict']}; deterministic {x['det']}" for x in sm["lost_or_added"]]
        L.append("")
    c = m["calls"]
    L += ["## Calls", "", "| call type | calls | fresh | median s | max s |", "|---|---|---|---|---|"]
    L += [f"| {k} | {v['n']} | {v['fresh']} | {v['median_s']} | {v['max_s']} |" for k, v in c["by_type"].items()]
    L += ["", f"Total {c['total']} calls ({c['fresh']} fresh), {c['failed']} failed, {c['total_latency_s']} s model time."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="stress-v1")
    ap.add_argument("--only", choices=["en", "ta", "hi", "simplify"])
    a = ap.parse_args()
    data = json.loads(STRESS.read_text(encoding="utf-8"))
    provider, calls, res = OllamaProvider(), [], {}
    t0 = time.perf_counter()
    if a.only in (None, "en"):
        print("English pairs", flush=True)
        res["en"] = evaluate_pairs(data["english_pairs"], "en", provider, calls)
    for lg in ("ta", "hi"):
        if a.only in (None, lg):
            print(lg, "pairs", flush=True)
            res[lg] = evaluate_pairs(data["translation_pairs"][lg], lg, provider, calls)
    if a.only in (None, "simplify"):
        print("simplifier", flush=True)
        res["simplifier"] = evaluate_simplifier(data["simplify_sources"], provider, calls)
    by = defaultdict(list)
    for c in calls:
        by[c["type"]].append(c)
    m = dict(run_id=a.run_id, model=provider.model, calls=dict(
        total=len(calls), fresh=sum(not c["cached"] for c in calls), failed=sum(bool(c["error"]) for c in calls), total_latency_s=round(sum(c["latency_s"] for c in calls)),
        by_type={k: dict(n=len(v), fresh=sum(not c["cached"] for c in v), median_s=round(statistics.median(c["latency_s"] for c in v), 1), max_s=round(max(c["latency_s"] for c in v), 1)) for k, v in by.items()}))
    for lg in ("en", "ta", "hi"):
        if lg in res:
            m[lg] = summarize_pairs(res[lg])
    if "simplifier" in res:
        sm = res["simplifier"]
        m["simplifier"] = {k: v for k, v in sm.items() if k != "rows"}
    raw_dir = REPO / "eval" / "runs" / a.run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "raw.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    out = REPO / "eval" / "results" / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "metrics.md").write_text(markdown(m), encoding="utf-8", newline="\n")
    print(f"done in {time.perf_counter() - t0:.0f}s: {len(calls)} calls")


if __name__ == "__main__":
    main()
