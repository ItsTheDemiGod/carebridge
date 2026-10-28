"""Phase 7c-lite: safety stress set through the REAL extraction (local Ollama), normalisation, safety engine and scripted confirmation overlay.
Protocol (pre-registered): docs/STRESS_EXTRACTION_PROTOCOL.md. Label for every output: stress set, authored, not tuned, not the test split.

  python -m eval.stress.run_stress_extraction --run-id stress-extraction-v1          # model calls; resumable from eval/runs/<run-id>/raw (gitignored)
  python -m eval.stress.run_stress_extraction --run-id stress-extraction-v1 --score-only   # no model call; scores the raw outputs already there

Additive: eval/stress/run_safety_stress.py (7a) is untouched. Images go only to the local Ollama adapter (extract_bytes, origin synthetic, no shared cache).
Committed output holds ids, categories and counts only; interaction levels appear only as aggregated counts (DDInter-derived, never pair by pair)."""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from app.safety import interactions as I  # noqa: E402
from app.safety.engine import analyse, med_inputs  # noqa: E402
from app.safety.names import canonical  # noqa: E402
from app.schemas.confirmation import Confirmations  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from app.services import confirmation as CF  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402
from eval.final_test.stats import BOOTSTRAP_N, BOOTSTRAP_SEED, bootstrap_ci, wilson  # noqa: E402
from eval.matching import NAME_THRESHOLD, med_similarity, one_to_one  # noqa: E402
from eval.phase4_safety import gt_duplicate_groups, gt_inputs  # noqa: E402
from eval.rescore import to_prediction  # noqa: E402
from eval.stress.run_safety_stress import CF_AS_LABEL, STRESS, best_formulary, formulary_id, load_stress, real_pairs  # noqa: E402

LABEL = "stress set, authored, not tuned, not the test split"
NAME_FLAGS = {"near_miss_name", "unresolved_name"}
SLOW_CALL_S = 120
OLLAMA = "http://127.0.0.1:11434"


# ------------------------------------------------------------------------------------------------------------ environment facts
def environment() -> dict:
    import httpx
    c = httpx.Client(timeout=30)
    ver = c.get(f"{OLLAMA}/api/version").json().get("version")
    from app.config import settings
    tags = {m["name"]: m["digest"] for m in c.get(f"{OLLAMA}/api/tags").json().get("models", [])}
    pin = json.loads((REPO / "eval/final_test/model_pin.json").read_text(encoding="utf-8"))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    from app.prompts import PROMPT_VERSION
    return dict(ollama_version_running=ver, ollama_version_pinned=pin["ollama_version"], model=settings.ollama_model, model_digest_running=tags.get(settings.ollama_model),
                model_digest_pinned=pin["model_digest"], digest_identical_to_pin=tags.get(settings.ollama_model) == pin["model_digest"],
                deviation="Ollama version differs from the pin (pin file unchanged); see docs/STRESS_EXTRACTION_PROTOCOL.md section 2",
                settings=dict(num_ctx=settings.ollama_num_ctx, num_predict=settings.ollama_num_predict, max_image_side=settings.ollama_max_image_side, temperature=0.0),
                extraction_prompt_version=PROMPT_VERSION, git_commit=commit, started=datetime.now().isoformat(timespec="seconds"))


def gpu_share() -> float | None:
    import httpx
    from app.config import settings
    c = httpx.Client(timeout=300)
    c.post(f"{OLLAMA}/api/generate", json=dict(model=settings.ollama_model, keep_alive=settings.ollama_keep_alive))  # load only
    for m in c.get(f"{OLLAMA}/api/ps").json().get("models", []):
        if m["name"] == settings.ollama_model and m.get("size"):
            return m["size_vram"] / m["size"]
    return None


# ------------------------------------------------------------------------------------------------------------ extraction (resumable)
def extract_all(raw_dir: Path, conds) -> tuple[dict, list]:
    from app.llm.ollama import OllamaProvider
    from app.services.extraction import extract_bytes
    provider = OllamaProvider()
    raw_dir.mkdir(parents=True, exist_ok=True)
    calls = dict(model_calls=0, resumed_from_disk=0)
    failures = []
    for cond in conds:
        for d, _ in load_stress():
            f = raw_dir / f"{cond}_{d['id']}.json"
            if f.exists():
                calls["resumed_from_disk"] += 1
                continue
            t0 = time.perf_counter()
            r = extract_bytes((STRESS / "rendered" / cond / f"{d['id']}.png").read_bytes(), "image/png", provider, origin="synthetic")
            calls["model_calls"] += 1
            rec = dict(ok=r.ok, error=r.error, latency_s=round(r.latency_s or time.perf_counter() - t0, 2), usage=r.usage, api_calls=r.api_calls,
                       output=r.output.model_dump(mode="json") if r.ok else None)
            f.write_text(json.dumps(rec), encoding="utf-8")
            print(f"{cond} {d['id']} ok={r.ok} {rec['latency_s']}s", flush=True)
            if not r.ok:
                failures.append(f"{cond}/{d['id']}: {r.error}")
            if rec["latency_s"] > SLOW_CALL_S:
                raise SystemExit(f"STOP: {cond}/{d['id']} took {rec['latency_s']} s (> {SLOW_CALL_S} s); raw output saved, tell the owner")
    return calls, failures


# ------------------------------------------------------------------------------------------------------------ scoring one document
def score_doc(d: dict, gt, out: ExtractionOutput, data) -> dict:
    G = from_ground_truth(gt).medications
    gin = gt_inputs(gt.medications)
    nd = normalise_document(out)
    P = nd.medications
    raw_pairs = one_to_one(len(G), len(out.medications), lambda i, j: med_similarity(G[i], out.medications[j]), NAME_THRESHOLD)
    npred = to_prediction(nd)
    pairs = one_to_one(len(G), len(P), lambda i, j: med_similarity(G[i], npred.medications[j]), NAME_THRESHOLD)  # (gt index, pred index)
    g2p, p2g = {i: j for i, j in pairs}, {j: i for i, j in pairs}
    c = Counter(gt_meds=len(G), pred_meds=len(P), tp_raw=len(raw_pairs), pred_raw=len(out.medications), tp_norm=len(pairs), hallucinated=len(P) - len(pairs))
    for m in P:
        c[f"review_{m.review_level}"] += 1
    grep, erep = analyse(gin, data), analyse(med_inputs(nd), data)
    eng = {(p.a, p.b): p for p in real_pairs(erep)}
    levels_gt, levels_found, causes, other = Counter(), Counter(), Counter(), Counter()
    for gp in real_pairs(grep):
        if gp.status != I.FOUND:
            continue
        c["gt_pairs"] += 1
        levels_gt[gp.level] += 1
        ra, rb = g2p.get(gp.a), g2p.get(gp.b)
        ep = eng.get(tuple(sorted((ra, rb)))) if ra is not None and rb is not None else None
        if ep is not None and ep.status == I.FOUND:
            c["found"] += 1
            levels_found[ep.level] += 1
            c["found_right_level"] += ep.level == gp.level
        else:
            c["strict_silent_misses"] += 1
            if ep is not None and ep.status == I.UNCONFIRMED:
                c["unconfirmed"] += 1
                for k in (ra, rb):
                    if not P[k].interaction_ready:
                        causes.update(CF.reason_ids(P[k]) or ["no_reason_listed"])
            else:
                c["silent_not_covered_by_flag"] += 1
                other["medicine_not_extracted" if ep is None else ep.status] += 1
    for p in real_pairs(erep):
        if p.status == I.FOUND:
            a, b = p2g.get(p.a), p2g.get(p.b)
            c["false_alarms"] += not (a is not None and b is not None and any(g.status == I.FOUND and {g.a, g.b} == {a, b} for g in real_pairs(grep)))
    # duplicates
    gdup = gt_duplicate_groups(gin)
    c["dup_gt_groups"] = len(gdup)
    c["dup_notices"] = len(erep.duplicate_notices)
    c["dup_groups_flagged"] = sum(any({p2g.get(k) for k in n.indices} == set(g) for n in erep.duplicate_notices) for g in gdup)
    # weekly / non-daily
    for i, g in enumerate(gt.medications):
        if g.frequency.times_per_day is None and not g.frequency.is_prn:
            c["nondaily_gt"] += 1
            j = g2p.get(i)
            if j is None:
                c["nondaily_not_extracted"] += 1
            else:
                c["nondaily_schedule_ready"] += bool(P[j].schedule_ready)
                c["nondaily_flagged"] += "non_daily_frequency" in P[j].flags
    # per-category checks
    cat = d["category"]
    if cat == "eye_drop_od" and 0 in g2p:
        m = P[g2p[0]]
        c["eye_extracted"] += 1
        c["eye_ambiguous_OD"] += "ambiguous_OD" in m.flags
        c["eye_schedule_ready"] += bool(m.schedule_ready)
        c["eye_interaction_ready"] += bool(m.interaction_ready)
        c["eye_any_flag"] += bool(m.flags)
    if cat == "eye_drop_od":
        c["eye_gt"] += 1
    unusual = [m for m in P if "unusual_strength" in m.flags]
    if cat == "unusual_strength":
        c["unusual_doc_flagged"] += bool(unusual)
    c["unusual_flags_total"] += len(unusual)
    garbled_gt = [i for i, x in enumerate(gin) if not x.interaction_ready]
    if cat == "garbled_name":
        c["garbled_gt"] += len(garbled_gt)
        for i in garbled_gt:
            j = g2p.get(i)
            if j is None:
                c["garbled_not_extracted"] += 1
            else:
                c["garbled_flagged"] += bool(set(P[j].flags) & NAME_FLAGS)
                c["garbled_interaction_ready"] += bool(P[j].interaction_ready)
    c["name_flags_total"] += sum(bool(set(m.flags) & NAME_FLAGS) for m in P)
    # P3: resolved_generic of interaction_ready medicines
    for j, m in enumerate(P):
        if m.interaction_ready:
            c["ir_total"] += 1
            if j in p2g:
                c["ir_wrong_generic"] += canonical(m.resolved_generic) != gin[p2g[j]].resolved_generic
            else:
                c["ir_without_gt_counterpart"] += 1
    # scripted overlay (ground-truth names; testing only)
    dec = []
    for j, m in enumerate(P):
        i = p2g.get(j)
        if i is None:
            dec.append(dict(index=j, action="remove"))
            continue
        reasons = CF.reason_ids(m)
        ack = [r for r in reasons if r not in CF.NAME_REASONS]
        fid = None
        if not m.interaction_ready and gin[i].interaction_ready and (best := best_formulary(gt.medications[i])):
            fid = formulary_id(best)
        dec.append(dict(index=j, action="select_formulary_drug", formulary_id=fid, strength_choice=CF_AS_LABEL, acknowledged_flags=ack) if fid
                   else dict(index=j, action="confirm_as_extracted", acknowledged_flags=ack))
    ov = CF.apply(nd, Confirmations.model_validate(dict(decisions=dec, added_medicines=[])))
    orep = analyse(med_inputs(ov.doc), data)
    o2g = {k: p2g.get(cm.source_index) for k, cm in enumerate(ov.meds)}
    ofound = {frozenset((o2g[p.a], o2g[p.b])): p.level for p in real_pairs(orep) if p.status == I.FOUND and o2g.get(p.a) is not None and o2g.get(p.b) is not None}
    ofalse = sum(p.status == I.FOUND and (o2g.get(p.a) is None or o2g.get(p.b) is None) for p in real_pairs(orep))
    extracted = {i for i in g2p}
    gt_ext = {frozenset((gp.a, gp.b)): gp.level for gp in real_pairs(grep) if gp.status == I.FOUND and gp.a in extracted and gp.b in extracted}
    c["ov_gt_pairs_extracted"] = len(gt_ext)
    c["ov_found_right_level"] = sum(ofound.get(k) == v for k, v in gt_ext.items())
    c["ov_false_alarms"] = sum(k not in gt_ext for k in ofound) + ofalse
    c["ov_equal_to_gt_mode"] = int(ofound == gt_ext)
    c["ov_newly_found"] = max(0, sum(k in ofound for k in gt_ext) - c["found"])
    row = dict(c)
    row["_levels_gt"], row["_levels_found"], row["_causes"], row["_other"] = dict(levels_gt), dict(levels_found), dict(causes), dict(other)
    row["_wrong_ir"] = c["ir_wrong_generic"]
    return row


# ------------------------------------------------------------------------------------------------------------ aggregation
def ratio(k, n):
    return None if not n else round(k / n, 4)


def pooled(rows: list[dict]) -> dict:
    s = Counter()
    lv = defaultdict(Counter)
    for r in rows:
        s.update({k: v for k, v in r.items() if not k.startswith("_") and isinstance(v, (int, bool))})
        for k in ("_levels_gt", "_levels_found", "_causes", "_other"):
            lv[k].update(r[k])
    s = Counter({k: int(v) for k, v in s.items()})
    out = dict(documents=len(rows), counts=dict(s), levels_ground_truth=dict(lv["_levels_gt"]), levels_found=dict(lv["_levels_found"]),
               unconfirmed_causes=dict(lv["_causes"]), other_outcomes=dict(lv["_other"]))
    docs = [Counter({k: int(v) for k, v in r.items() if not k.startswith("_") and isinstance(v, (int, bool))}) for r in rows]

    for nm, tp, pr, gtm in (("raw", "tp_raw", "pred_raw", "gt_meds"), ("normalised", "tp_norm", "pred_meds", "gt_meds")):
        out[f"precision_{nm}"] = _prop(s[tp], s[pr], docs, tp, pr)
        out[f"recall_{nm}"] = _prop(s[tp], s[gtm], docs, tp, gtm)
        f1 = lambda t, tp=tp, pr=pr: (2 * t[tp] / (t[pr] + t["gt_meds"])) if (t[pr] + t["gt_meds"]) else None  # noqa: E731
        out[f"f1_{nm}"] = dict(k=2 * s[tp], n=s[pr] + s["gt_meds"], value=_r1(f1(s)), bootstrap95=_r(bootstrap_ci(docs, f1)))
    out["found_rate"] = _prop(s["found"], s["gt_pairs"], docs, "found", "gt_pairs")
    out["found_right_level_rate"] = _prop(s["found_right_level"], s["gt_pairs"], docs, "found_right_level", "gt_pairs")
    return out


def _r(t):
    return None if t is None else [round(t[0], 4), round(t[1], 4)]


def _r1(v):
    return None if v is None else round(v, 4)


def _prop(k, n, docs, nk, dk):
    return dict(k=k, n=n, value=ratio(k, n), wilson95=_r(wilson(k, n)), bootstrap95=_r(bootstrap_ci(docs, lambda t: t[nk] / t[dk] if t[dk] else None)))


def criteria(by_cond: dict) -> dict:
    allrows = [r for cond in by_cond.values() for r in cond["_rows"]]
    s = Counter()
    for r in allrows:
        s.update({k: v for k, v in r.items() if not k.startswith("_") and isinstance(v, (int, bool))})
    p4_gt, p4_ok = s["ov_gt_pairs_extracted"], s["ov_found_right_level"]
    return dict(
        P1_silent_misses_not_covered_by_flag=dict(value=s["silent_not_covered_by_flag"], of_gt_pairs=s["gt_pairs"], passed=s["silent_not_covered_by_flag"] == 0),
        P2_nondaily_schedule_ready=dict(value=s["nondaily_schedule_ready"], of_nondaily_extracted=s["nondaily_gt"] - s["nondaily_not_extracted"], nondaily_in_ground_truth=s["nondaily_gt"], passed=s["nondaily_schedule_ready"] == 0),
        P3_wrong_resolved_generic_among_interaction_ready=dict(value=s["ir_wrong_generic"], of_interaction_ready=s["ir_total"], interaction_ready_without_gt_counterpart_reported_separately=s["ir_without_gt_counterpart"], passed=s["ir_wrong_generic"] == 0),
        P4_overlay_every_extracted_gt_pair_found_at_right_level=dict(value=p4_ok, of=p4_gt, passed=p4_ok == p4_gt),
        scope="both conditions together, all documents scored; per-condition figures are in conditions.<cond>.pooled")


def per_category(rows_with_cat: list[tuple[str, dict]]) -> dict:
    cats = defaultdict(list)
    for cat, r in rows_with_cat:
        cats[cat].append(r)
    keys = ["gt_meds", "pred_meds", "tp_raw", "tp_norm", "hallucinated", "review_must_confirm", "review_note", "review_none", "gt_pairs", "found", "found_right_level", "unconfirmed",
            "silent_not_covered_by_flag", "false_alarms", "dup_gt_groups", "dup_groups_flagged", "dup_notices", "nondaily_gt", "nondaily_not_extracted", "nondaily_schedule_ready", "nondaily_flagged",
            "eye_gt", "eye_extracted", "eye_ambiguous_OD", "eye_schedule_ready", "unusual_doc_flagged", "garbled_gt", "garbled_flagged", "garbled_not_extracted", "garbled_interaction_ready",
            "ir_total", "ir_wrong_generic", "ov_gt_pairs_extracted", "ov_found_right_level", "ov_false_alarms", "ov_equal_to_gt_mode"]
    out = {}
    for cat, rs in cats.items():
        p = pooled(rs)
        out[cat] = dict(documents=len(rs), **{k: p["counts"].get(k, 0) for k in keys}, levels_ground_truth=p["levels_ground_truth"], levels_found=p["levels_found"],
                        unconfirmed_causes=p["unconfirmed_causes"], other_outcomes=p["other_outcomes"])
    return out


# ------------------------------------------------------------------------------------------------------------ outputs
def md(m: dict) -> str:
    e = m["environment"]
    L = [f"# Stress extraction results ({m['run_id']})", "", f"**{LABEL}.** 30 authored synthetic prescriptions, clean and photo renders. 30 documents give WIDE intervals; no figure here is a claim of accuracy, reliability or safety.", "",
         f"- Ollama running **{e['ollama_version_running']}**, pinned (official final run) **{e['ollama_version_pinned']}** (stated deviation; the pin file is unchanged; stress numbers are not to be compared directly with the official ones).",
         f"- Model {e['model']}, digest running `{e['model_digest_running']}` (identical to the pin: {e['digest_identical_to_pin']}).",
         f"- Settings {e['settings']}, extraction prompt {e['extraction_prompt_version']}, git commit `{e['git_commit'][:10]}`, started {e['started']}.", "",
         "## Pass criteria (pre-registered, both conditions together)", "", "| criterion | result | passed |", "|---|---|---|"]
    for k, v in m["criteria"].items():
        if isinstance(v, dict):
            L.append(f"| {k} | {', '.join(f'{a}={b}' for a, b in v.items() if a != 'passed')} | **{v['passed']}** |")
    for cond, c in m["conditions"].items():
        p = c["pooled"]
        L += ["", f"## Condition `{cond}` ({p['documents']} documents scored; failed or skipped: {len(c['failed'])})", ""]
        for k in ("precision_raw", "recall_raw", "f1_raw", "precision_normalised", "recall_normalised", "f1_normalised", "found_rate", "found_right_level_rate"):
            v = p[k]
            L.append(f"- {k}: {v['k']}/{v['n']} = {v['value']}, Wilson {v.get('wilson95')}, document bootstrap {v.get('bootstrap95')}")
        L.append(f"- counts: {p['counts']}")
        L.append(f"- ground-truth pair levels: {p['levels_ground_truth']}; found levels: {p['levels_found']}; unconfirmed causes: {p['unconfirmed_causes']}; other outcomes: {p['other_outcomes']}")
        L += ["", "| category | docs | gt meds | detected (norm) | halluc. | gt pairs | found | unconfirmed | silent not flag-covered | false alarms | overlay right/of |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for cat, v in c["by_category"].items():
            L.append(f"| {cat} | {v['documents']} | {v['gt_meds']} | {v['tp_norm']} | {v['hallucinated']} | {v['gt_pairs']} | {v['found']} | {v['unconfirmed']} | {v['silent_not_covered_by_flag']} | {v['false_alarms']} | {v['ov_found_right_level']}/{v['ov_gt_pairs_extracted']} |")
    L += ["", f"Run facts: {m['run_facts']}", ""]
    return "\n".join(L) + "\n"


def csv_rows(by_cond) -> list[dict]:
    cols = ["gt_meds", "pred_meds", "tp_raw", "tp_norm", "hallucinated", "review_must_confirm", "review_note", "review_none", "gt_pairs", "found", "found_right_level", "unconfirmed",
            "silent_not_covered_by_flag", "false_alarms", "dup_gt_groups", "dup_groups_flagged", "nondaily_gt", "nondaily_schedule_ready", "eye_ambiguous_OD", "eye_schedule_ready",
            "unusual_doc_flagged", "garbled_gt", "garbled_flagged", "ir_wrong_generic", "ov_gt_pairs_extracted", "ov_found_right_level", "ov_equal_to_gt_mode"]
    out = []
    for cond, c in by_cond.items():
        for (d, r) in c["_docs"]:
            out.append(dict(condition=cond, id=d["id"], category=d["category"], status="scored", **{k: r.get(k, 0) for k in cols}))
        for f in c["failed"]:
            out.append(dict(condition=cond, id=f.split(":")[0].split("/")[1], category="", status="failed: " + f.split(": ", 1)[1]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="stress-extraction-v1")
    ap.add_argument("--conds", default="clean,photo")
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args(argv)
    conds = a.conds.split(",")
    res_dir, raw_dir = REPO / "eval/results" / a.run_id, REPO / "eval/runs" / a.run_id / "raw"
    if res_dir.exists() and (res_dir / "SHA256SUMS").exists():
        raise SystemExit(f"{res_dir} is a finished, read-only result folder; a re-run needs a new --run-id and is post-hoc")
    data = I.load_data()
    if data.store is None:
        raise SystemExit("the local interaction store is missing")
    env = environment()
    facts = dict(model_calls=0, resumed_from_disk=0)
    t0 = time.time()
    if not a.score_only:
        share = gpu_share()
        env["gpu_share_at_start"] = share
        print(f"GPU share {share}", flush=True)
        if share is None or share < 0.8:
            raise SystemExit("STOP: less than 80 percent of the model is on the GPU (or not loaded)")
        facts, _ = extract_all(raw_dir, conds)
    env["finished"] = datetime.now().isoformat(timespec="seconds")
    facts["duration_s_this_invocation"] = round(time.time() - t0, 1)
    by_cond = {}
    for cond in conds:
        rows, docs, failed, lat = [], [], [], []
        for d, gt in load_stress():
            rec = json.loads((raw_dir / f"{cond}_{d['id']}.json").read_text(encoding="utf-8"))
            lat.append(rec["latency_s"])
            if not rec["ok"]:
                failed.append(f"{cond}/{d['id']}: {rec['error']}")
                continue
            r = score_doc(d, gt, ExtractionOutput.model_validate(rec["output"]), data)
            rows.append(r)
            docs.append((d, r))
        by_cond[cond] = dict(pooled=pooled(rows), by_category=per_category([(d["category"], r) for d, r in docs]), failed=failed,
                             latency_s=dict(n=len(lat), mean=round(sum(lat) / len(lat), 1), max=max(lat), total=round(sum(lat), 1)), _rows=rows, _docs=docs)
    m = dict(run_id=a.run_id, label=LABEL, protocol="docs/STRESS_EXTRACTION_PROTOCOL.md", environment=env, run_facts=facts, bootstrap=dict(n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED),
             criteria=criteria(by_cond), conditions={k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in by_cond.items()})
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "metrics.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8", newline="\n")
    (res_dir / "metrics.md").write_text(md(m), encoding="utf-8", newline="\n")
    (res_dir / "run_manifest.json").write_text(json.dumps(dict(run_id=a.run_id, label=LABEL, environment=env, run_facts=facts, protocol="docs/STRESS_EXTRACTION_PROTOCOL.md",
                                                               conditions=conds, failed={k: v["failed"] for k, v in by_cond.items()}, latency={k: v["latency_s"] for k, v in by_cond.items()}), indent=1) + "\n", encoding="utf-8", newline="\n")
    rows = csv_rows(by_cond)
    fields = sorted({k for r in rows for k in r}, key=lambda k: (["condition", "id", "category", "status"].index(k) if k in ("condition", "id", "category", "status") else 9, k))
    with (res_dir / "per_document.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, restval="")
        w.writeheader()
        w.writerows(rows)
    sums = [f"{hashlib.sha256((res_dir / n).read_bytes()).hexdigest()}  {n}" for n in ("metrics.json", "metrics.md", "per_document.csv", "run_manifest.json")]
    (res_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(m["criteria"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
