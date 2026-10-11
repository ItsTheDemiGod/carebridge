"""How well does the verifier catch known faults? Per corruption type: detection by the deterministic checks alone, the judge alone and both,
plus the false-reject rate on uncorrupted lines.   python -m eval.corruption_eval --run-id phase3-dev-clean [--prompt-version v1]

Model calls are batched per document and language (chunks of 10) and cached, so a rerun is free. Dev split only, local Ollama only.
Writes eval/results/<run-id>/corruptions.json.
For Tamil and Hindi only number_changed, drug_name_swapped, wrong_script and item_dropped are generated; negation and urgency changes cannot be
generated or checked deterministically in those languages and rely on the back-translation judge and native review (not measured here).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.llm.ollama import OllamaProvider  # noqa: E402
from app.services import narrative as nv  # noqa: E402
from app.services.verification import deterministic  # noqa: E402
from eval.make_corruptions import build, load_pool, probe_pool  # noqa: E402

CHUNK = 10


def chunks(xs, n=CHUNK):
    return [xs[i:i + n] for i in range(0, len(xs), n)]


def judge_variants(variants: list[dict], lang: str, provider, version: str, calls: list):
    """Fill v['judge'] = (verdict, reason) or None. ta/hi: back-translate first, judge the back-translation."""
    by_doc = defaultdict(list)
    for v in variants:
        by_doc[v["doc"]].append(v)
    for doc, vs in sorted(by_doc.items()):
        for ch in chunks(vs):
            cands = {v["vid"]: v["text"] for v in ch}
            if lang != "en":
                st = nv.back_translate(cands, lang, provider, version=version)
                calls.append(st.call)
                for v in ch:
                    v["back"] = st.values.get(v["vid"])
                cands = {k: v for k, v in ((v["vid"], v["back"]) for v in ch) if v}
            st = nv.judge({v["vid"]: (v["source"], cands[v["vid"]]) for v in ch if v["vid"] in cands}, lang, provider, version=version)
            calls.append(st.call)
            for v in ch:
                v["judge"] = st.values.get(v["vid"]) if st.ok else None


def det_fail(v: dict) -> bool:
    ref = v.get("plain") if v["lang"] != "en" else None
    res, _ = deterministic(v["kind"], v["source"], v["text"], v["lang"], number_ref=ref, english_view=v.get("back") if v["lang"] != "en" else None)
    v["det"] = res
    return not all(res.values())


def rate(a, b):
    return None if not b else round(a / b, 3)


def summarise(variants: list[dict]) -> dict:
    out = {}
    for key in sorted({(v["lang"], v["type"]) for v in variants}):
        g = [v for v in variants if (v["lang"], v["type"]) == key]
        det = sum(v["det_fail"] for v in g)
        jd = [v for v in g if v.get("judge") is not None]
        judge = sum(v["judge"][0] != "supported" for v in jd)
        both = sum(v["det_fail"] or (v.get("judge") is not None and v["judge"][0] != "supported") for v in g)
        out[f"{key[0]}/{key[1]}"] = dict(n=len(g), deterministic=rate(det, len(g)), judge=rate(judge, len(jd)), judge_n=len(jd), combined=rate(both, len(g)),
                                         missed_by_both=[dict(doc=v["doc"], line=v["item_id"], text=v["text"][:90], verdict=(v.get("judge") or [None])[0]) for v in g
                                                         if not v["det_fail"] and not (v.get("judge") and v["judge"][0] != "supported")][:3])
    return out


def item_dropped_detection(pool: list[dict]) -> dict:
    """Remove one id from the model's output: the id-integrity check must flag exactly that id. The judge never receives a missing item (n/a)."""
    n = hit = 0
    for doc in sorted({p["doc"] for p in pool}):
        ids = [p["item_id"] for p in pool if p["doc"] == doc]
        for drop in ids:
            _, problems, batch = nv.reconcile(ids, [i for i in ids if i != drop])
            n += 1
            hit += problems.get(drop) == "id_missing" and not batch
    return dict(n=n, deterministic=rate(hit, n), judge=None, combined=rate(hit, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="phase3-dev-clean")
    ap.add_argument("--prompt-version", default=nv.PROMPT_VERSION)
    a = ap.parse_args()
    pool = load_pool(a.run_id)
    assert pool, "run eval.run_narrative first"
    variants = build(pool + probe_pool())  # probes only add English variants for drug_name_swapped and urgency_dropped (and a few others)
    provider, calls = OllamaProvider(), []
    for lang in ("en", "ta", "hi"):
        vs = [v for v in variants if v["lang"] == lang]
        judge_variants(vs, lang, provider, a.prompt_version, calls)
        print(f"{lang}: {len(vs)} corrupted variants judged", flush=True)
    for v in variants:
        v["det_fail"] = det_fail(v)

    # false rejects on uncorrupted lines. identity: the source line itself as the candidate (a perfect candidate). model_plain: the model's own plain English (includes true model errors)
    ident = [dict(vid=f"{p['item_id']}~identity", doc=p["doc"], item_id=p["item_id"], kind=p["kind"], lang="en", type="identity", source=p["source"], text=p["source"]) for p in pool]
    judge_variants(ident, "en", provider, a.prompt_version, calls)
    for v in ident:
        v["det_fail"] = det_fail(v)
    fr = dict(n=len(ident), deterministic=rate(sum(v["det_fail"] for v in ident), len(ident)), judge=rate(sum(bool(v["judge"]) and v["judge"][0] != "supported" for v in ident), len(ident)),
              combined=rate(sum(v["det_fail"] or (bool(v["judge"]) and v["judge"][0] != "supported") for v in ident), len(ident)))
    plain_lines = [p for p in pool if p["plain"]]
    result = dict(run_id=a.run_id, seed=__import__("eval.make_corruptions", fromlist=["SEED"]).SEED, cap_per_type=40, by_type=summarise(variants),
                  item_dropped=item_dropped_detection(pool), false_reject_identity=fr,
                  model_plain_english_reject_rate=dict(n=len(plain_lines), rejected=sum(not p["plain_verified"] for p in plain_lines), note="includes real model errors, so it is not a false-reject rate"),
                  judge_calls=dict(n=len(calls), fresh=sum(not c.cached for c in calls), errors=[c.error for c in calls if c.error]))
    out = REPO / "eval" / "results" / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "corruptions.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: {m: x[m] for m in ("n", "deterministic", "judge", "combined")} for k, x in result["by_type"].items()}, indent=0)[:3000])
    print("false_reject_identity", fr)


if __name__ == "__main__":
    main()
