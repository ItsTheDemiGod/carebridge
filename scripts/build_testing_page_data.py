"""Phase 6d: writes frontend/src/data/testing.generated.json, the figures of the "How we tested it" page.   python scripts/build_testing_page_data.py [--check]

Reads ONLY small committed files (listed in SOURCES and in docs/TESTING_PAGE.md); every number on the page comes from here, none is typed into a string
(strings carry {placeholders} that are filled from each entry's params). Fails loudly when a file, key or expected property is missing. No model, no network.
Each entry: id, group, label (string id), value, unit (ratio | count), source (committed file), measures (string id), data (string id) + params, caveat (string id or null),
split (dev | test), date (the day the source file was committed; the metrics files carry no date of their own, see RUN_DATES), plus optional n/of for "k of n" figures.
Phase 7b write-up: the held-out TEST figures come from eval/results/final-test-v1/metrics.json (read-only, official run); the builder verifies that folder's
SHA256SUMS first and fails when a file differs. Each test row carries value, n/of, interval (Wilson or document bootstrap, taken from the file or computed here with
the same formula), the DEV value of the same measure from the file's own dev_vs_test table when it has one, source, split and run date (from the committed audit copy
of eval/test_runs.log). Rows are never selected: every primary metric of the protocol is listed (pooled); per-condition detail is named under "also measured".
--check compares with the committed file (staleness test)."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "frontend" / "src" / "data" / "testing.generated.json"
FT = "eval/results/final-test-v1"  # the official one-shot run (never edited; SHA256SUMS verified below)
FT_METRICS = f"{FT}/metrics.json"
FT_AUDIT_LOG = "eval/results/final-test-v1-audit/test_runs.log"  # committed copy of the gitignored eval/test_runs.log
SCRIPT_VERSION = "2"

N2 = "eval/results/dev-ollama-v1-normalised-v2/metrics.json"  # Phase 2 raw output re-scored with the rules (2h/2i), 20 dev documents x 5 image conditions
P3E = "eval/results/phase3e-dev-clean/metrics.json"  # Phase 3e: free-text lines shown per language (dev, clean images)
STRESS = "eval/results/stress-v1/metrics.json"  # Phase 3e blind stress set (authored correct and wrong lines)
P4 = "eval/results/phase4-dev-with-supplement/metrics.json"  # Phase 4 safety layer with the author-checked supplement enabled
LIVE = "docs/smoke/phase6d_live.json"  # Phase 6d: three end-to-end runs of the real app (JSON lines; flow 2 is the first of three traced re-runs, see PROGRESS.md)
FORMULARY = "data/reference/formulary.json"
SS = "eval/results/stress-extraction-v1"  # Phase 7c-lite: the authored safety stress set through the real extraction (never edited; SHA256SUMS verified below)
SS_METRICS = f"{SS}/metrics.json"
SOURCES = [N2, P3E, STRESS, P4, LIVE, FORMULARY, FT_METRICS, SS_METRICS]
# the day each source file was first committed (git log --diff-filter=A); the files themselves hold no date
RUN_DATES = {N2: "2026-10-10", P3E: "2026-10-16", STRESS: "2026-10-16", P4: "2026-10-16", LIVE: "2026-10-18"}


def load(path: str):
    p = REPO / path
    if not p.exists():
        raise SystemExit(f"missing source file: {path}")
    text = p.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()] if path == LIVE else json.loads(text)


def dig(obj, *keys, src: str):
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            raise SystemExit(f"{src}: missing field {'.'.join(map(str, keys))} (stopped at {k!r})")
        obj = obj[k]
    return obj


Z95 = 1.959963984540054


def wilson(k: int, n: int) -> list[float]:
    p, d = k / n, 1 + Z95 * Z95 / n
    c, h = (p + Z95 * Z95 / (2 * n)) / d, Z95 * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def verify_final_folder() -> None:
    """The official results folder must be byte-identical to what was committed (either line ending accepted: a Windows checkout may convert them, and per_document.csv is written with CRLF)."""
    root = REPO / FT
    sums = (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    if not sums:
        raise SystemExit(f"{FT}/SHA256SUMS is empty")
    for line in sums:
        digest, name = line.split(maxsplit=1)
        name = name.strip().lstrip("*")
        raw = (root / name).read_bytes()
        lf = raw.replace(b"\r\n", b"\n")
        if digest not in {hashlib.sha256(x).hexdigest() for x in (raw, lf, lf.replace(b"\n", b"\r\n"))}:
            raise SystemExit(f"{FT}/{name} does not match SHA256SUMS: the official results were changed")


def run_date() -> str:
    for line in (REPO / FT_AUDIT_LOG).read_text(encoding="utf-8").splitlines():
        if "start run_id=final-test-v1 official=True" in line:
            return line[:10]
    raise SystemExit(f"{FT_AUDIT_LOG}: no official start entry")


def test_section() -> dict:
    """Every primary metric of docs/FINAL_TEST_PROTOCOL.md, pooled over the five conditions (per-condition detail is in docs/FINAL_TEST_RESULTS.md)."""
    m = load(FT_METRICS)
    if not m.get("official") or m.get("split") != "test":
        raise SystemExit(f"{FT_METRICS}: not the official test run")
    date = run_date()
    dev = {r["metric"]: r["dev"] for r in m["dev_vs_test"]}
    ops, fl, sf, ex = m["operational"]["all"], m["flags"]["all"], m["safety"], m["explanation"]
    conds = list(m["conditions"])
    entries: list[dict] = []

    def add(id, group, label, measures, value, unit, n=None, of=None, ci=None, ci_kind=None, dev_key=None, params=None):
        e = {"id": id, "group": group, "label": label, "params": params or {}, "measures": measures, "value": value, "unit": unit, "source": FT_METRICS, "split": "test", "date": date}
        if of is not None:
            e["n"], e["of"] = n, of
        if ci:
            e["ci"], e["ci_kind"] = ci, ci_kind
        if dev_key is not None:
            dv = dig(dev, dev_key, src=f"{FT_METRICS} dev_vs_test")
            e["dev"] = dv
            if ci and unit == "ratio":
                e["dev_outside"] = bool(dv < ci[0] - 5e-5 or dv > ci[1] + 5e-5)
        entries.append(e)

    T, MM, FLD = "ui.testing.t.f.", "ui.testing.t.m.", "ui.testing.t.fld."
    for key, grp, sfx in (("raw", "ex_raw", "raw"), ("normalised", "ex_norm", "norm")):
        a = dig(m, "extraction", key, "all", src=FT_METRICS)
        c, iv = a["counts"], a["intervals"]
        listed, real = c["med_tp"] + c["med_fp"], c["med_tp"] + c["med_fn"]

        def dk(base, key=key):
            return f"{base}, {key}"
        add(f"t_prec_{sfx}", grp, T + "precision", MM + "precision", a["med_precision"], "ratio", c["med_tp"], listed, iv["med_precision"], "wilson")
        add(f"t_rec_{sfx}", grp, T + "recall", MM + "recall", a["med_recall"], "ratio", c["med_tp"], real, iv["med_recall"], "wilson")
        add(f"t_f1_{sfx}", grp, T + "f1", MM + "f1", a["med_f1"], "ratio", ci=iv["med_f1_bootstrap"], ci_kind="bootstrap", dev_key=dk("medicine F1"))
        add(f"t_every_{sfx}", grp, T + "every", MM + "every", a["med_fully_correct_rate"], "ratio", c["med_fully_correct"], c["med_tp"], iv["med_fully_correct_rate_bootstrap"], "bootstrap", dk("fully-correct medicine rate"))
        add(f"t_hall_{sfx}", grp, T + "hall", MM + "hall", a["hallucinated_meds"], "count", a["hallucinated_meds"], listed)
        add(f"t_inv_{sfx}", grp, T + "inv", MM + "inv", a["invented_value_rate"], "ratio", c["invented"], c["null_total"], iv["invented_value_rate"], "wilson", dk("invented-value rate"))
        for f in ("strength", "form", "dose", "times_per_day", "timing_label", "is_prn", "duration_days", "brand_name", "generic_name"):
            dkf = dk(f"{f.replace('_', ' ')} field") if f in ("timing_label", "brand_name") else None
            add(f"t_{f}_{sfx}", grp, T + "field", MM + "field", a[f"acc_{f}"], "ratio", ci=iv[f"acc_{f}"], ci_kind="wilson", dev_key=dkf, params={"field": FLD + f})
    meds = fl["medicines"]
    add("t_must", "flags", T + "must", MM + "must", fl["share_must_confirm"], "ratio", fl["must_confirm"], meds, fl["share_must_confirm_ci"], "wilson", "share of medicines at must_confirm")
    add("t_nameerr", "flags", T + "nameerr", MM + "nameerr", fl["name_errors_remaining"], "count", fl["name_errors_remaining"], meds)
    add("t_nameunfl", "flags", T + "nameunfl", MM + "nameunfl", fl["name_errors_unflagged"], "count", fl["name_errors_unflagged"], fl["name_errors_remaining"], dev_key="name errors remaining, unflagged")
    add("t_timeunfl", "flags", T + "timeunfl", MM + "timeunfl", fl["timing_errors_unflagged"], "count", fl["timing_errors_unflagged"], fl["timing_errors_remaining"])
    add("t_intready", "flags", T + "intready", MM + "intready", fl["interaction_ready"], "count", fl["interaction_ready"], meds)
    add("t_schedready", "flags", T + "schedready", MM + "schedready", fl["schedule_ready"], "count", fl["schedule_ready"], meds)
    add("t_wrongid", "flags", T + "wrongid", MM + "wrongid", fl["wrong_resolved_generic"], "count", fl["wrong_resolved_generic"], fl["interaction_ready"], fl["wrong_resolved_generic_ci"], "wilson", "wrong resolved_generic among interaction_ready")
    add("t_wrongsched", "flags", T + "wrongsched", MM + "wrongsched", fl["wrong_schedule"], "count", fl["wrong_schedule"], fl["schedule_ready"], fl["wrong_schedule_ci"], "wilson")
    s = sf["safety"]
    known = sf["ground_truth"]["statuses"]["interaction_found"] * len(conds)
    allpairs = sf["ground_truth"]["pairs"] * len(conds)
    add("t_strict", "safety", T + "strict", MM + "strict", s["silent_misses_strict"], "count", s["silent_misses_strict"], known, dev_key="silent misses, strict")
    add("t_silent", "safety", T + "silent", MM + "silent", s["silent_misses_not_covered_by_a_flag"], "count", s["silent_misses_not_covered_by_a_flag"], known, dev_key="silent misses not covered by a flag")
    add("t_false", "safety", T + "false", MM + "false", s["false_alarms"], "count", s["false_alarms"], allpairs, dev_key="false alarms")
    for c in conds:
        st = sf["pair_statuses_by_condition"][c]
        nc, tot = st["not_checked_unconfirmed"] + st["not_checked_no_record"], sum(st.values())
        if abs(nc / tot - sf["share_not_checked_by_condition"][c]) > 6e-4:
            raise SystemExit(f"{FT_METRICS}: share not checked ({c}) does not follow from the status counts")
        add(f"t_nc_{c}", "safety", T + "nc", MM + "nc", sf["share_not_checked_by_condition"][c], "ratio", nc, tot, wilson(nc, tot), "wilson", params={"cond": "ui.testing.t.cond." + c})
    kinds = {"all": ex["lines"], **ex["lines_by_kind"]}
    for lang in ("en", "ta", "hi"):
        for kind, nk in kinds.items():
            v = ex["verified_share"][lang][kind]
            k = round(v * nk)
            if abs(k / nk - v) > 6e-4:
                raise SystemExit(f"{FT_METRICS}: verified share {lang}/{kind} is not a whole number of {nk} lines")
            add(f"t_ver_{lang}_{kind}", "expl", T + "ver", MM + "ver", v, "ratio", k, nk, wilson(k, nk), "wilson", params={"lang": "ui.testing.t.lang." + lang, "kind": "ui.testing.t.kind." + kind})
    for lang in ("en", "ta", "hi"):
        v = dig(ex, "provenance_share", lang, "all", "shown_in_language", src=FT_METRICS)
        k = round(v * ex["lines"])
        add(f"t_shown_{lang}", "expl", T + "shown", MM + "shown", v, "ratio", k, ex["lines"], wilson(k, ex["lines"]), "wilson", f"share of free-text lines shown in {lang}", {"lang": "ui.testing.t.lang." + lang})
    add("t_att", "ops", T + "att", MM + "att", ops["attempted"], "count")
    add("t_sco", "ops", T + "sco", MM + "sco", ops["scored"], "count", ops["scored"], ops["attempted"])
    add("t_skip", "ops", T + "skip", MM + "skip", ops["skipped"], "count", ops["skipped"], ops["attempted"])
    add("t_med", "ops", T + "med", MM + "med", ops["latency_median_s"], "seconds")
    add("t_p95", "ops", T + "p95", MM + "p95", ops["latency_p95_s"], "seconds")
    cr = m["extraction"]["raw"]["all"]["counts"]
    params = {"docs": m["documents"], "conditions": len(conds), "runs": ops["attempted"], "mentions": cr["med_tp"] + cr["med_fn"], "lines": ex["lines"], "pairs": allpairs, "scored": ops["scored"], "skipped": ops["skipped"], "date": date, "level": 95}
    gids = ["ex_raw", "ex_norm", "flags", "safety", "expl", "ops"]
    if {e["group"] for e in entries} != set(gids):
        raise SystemExit("test groups out of sync")
    return {"run": True, "date": date, "source": FT_METRICS, "params": params, "groups": gids, "entries": entries,
            "also": {"doc": "docs/FINAL_TEST_RESULTS.md", "source": FT_METRICS, "per_doc": f"{FT}/per_document.csv"}}


def verify_stress_folder() -> None:
    root = REPO / SS
    sums = (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    if not sums:
        raise SystemExit(f"{SS}/SHA256SUMS is empty")
    for line in sums:
        digest, name = line.split(maxsplit=1)
        raw = (root / name.strip().lstrip("*")).read_bytes()
        lf = raw.replace(b"\r\n", b"\n")
        if digest not in {hashlib.sha256(x).hexdigest() for x in (raw, lf, lf.replace(b"\n", b"\r\n"))}:
            raise SystemExit(f"{SS}/{name} does not match SHA256SUMS: the stress results were changed")


def stress_section() -> dict:
    """The pre-registered metrics of docs/STRESS_EXTRACTION_PROTOCOL.md, pooled per render condition (per-category tables and the cause of each held-back pair stay in docs/STRESS_RESULTS.md).
    Every figure is k of n with a Wilson interval; the document bootstrap is added where the metrics file has one."""
    verify_stress_folder()
    m = load(SS_METRICS)
    man = load(f"{SS}/run_manifest.json")
    if m.get("label") != "stress set, authored, not tuned, not the test split":
        raise SystemExit(f"{SS_METRICS}: unexpected label")
    conds = list(m["conditions"])
    env = man["environment"]
    pooled = {c: m["conditions"][c]["pooled"] for c in conds}
    cn = {c: pooled[c]["counts"] for c in conds}
    g = lambda c, k: cn[c].get(k, 0)  # noqa: E731  (a Counter omits zero counts)
    docs = pooled[conds[0]]["documents"]
    crit = m["criteria"]
    entries: list[dict] = []

    def cell(k, n, boot=None):
        return {"k": k, "n": n, "value": round(k / n, 4) if n else None, "wilson": wilson(k, n) if n else None, "bootstrap": boot}

    def add(id, group, label, fn, params=None, passed=None, limit=None, no_kn=False):
        e = {"id": id, "group": group, "label": "ui.testing.s.f." + label, "measures": "ui.testing.s.m." + label, "params": params or {}, "cells": {c: fn(c) for c in conds},
             "source": SS_METRICS, "split": "stress", "date": env["started"][:10]}
        if no_kn:
            e["no_kn"] = True
        if passed is not None:
            e["passed"], e["limit"] = passed, limit
        entries.append(e)

    P = lambda name: crit[name]["passed"]  # noqa: E731
    add("p1", "crit", "p1", lambda c: cell(g(c, "silent_not_covered_by_flag"), g(c, "gt_pairs")), passed=P("P1_silent_misses_not_covered_by_flag"), limit="zero")
    add("p2", "crit", "p2", lambda c: cell(g(c, "nondaily_schedule_ready"), g(c, "nondaily_gt") - g(c, "nondaily_not_extracted")), passed=P("P2_nondaily_schedule_ready"), limit="zero")
    add("p3", "crit", "p3", lambda c: cell(g(c, "ir_wrong_generic"), g(c, "ir_total")), passed=P("P3_wrong_resolved_generic_among_interaction_ready"), limit="zero")
    add("p4", "crit", "p4", lambda c: cell(g(c, "ov_found_right_level"), g(c, "ov_gt_pairs_extracted")), passed=P("P4_overlay_every_extracted_gt_pair_found_at_right_level"), limit="all")
    for key, grp in (("raw", "detect_raw"), ("normalised", "detect_norm")):
        for name in ("precision", "recall"):
            add(f"{name}_{key}", grp, name, lambda c, name=name, key=key: cell(pooled[c][f"{name}_{key}"]["k"], pooled[c][f"{name}_{key}"]["n"], pooled[c][f"{name}_{key}"]["bootstrap95"]))
        add(f"f1_{key}", grp, "f1", lambda c, key=key: {"k": None, "n": None, "value": pooled[c][f"f1_{key}"]["value"], "wilson": None, "bootstrap": pooled[c][f"f1_{key}"]["bootstrap95"]}, no_kn=True)
    add("hall", "detect_norm", "hall", lambda c: cell(g(c, "hallucinated"), g(c, "pred_meds")))
    for lvl in ("must_confirm", "note", "none"):
        add(f"review_{lvl}", "review", "review_" + lvl, lambda c, lvl=lvl: cell(g(c, f"review_{lvl}"), g(c, "gt_meds") + g(c, "hallucinated")))
    levels = ("major", "moderate", "minor", "unknown")
    for lvl in levels:
        add(f"gt_{lvl}", "inter", "gt_level", lambda c, lvl=lvl: cell(pooled[c]["levels_ground_truth"].get(lvl, 0), g(c, "gt_pairs")), params={"level": "ui.testing.s.lvl." + lvl})
    add("found", "inter", "found", lambda c: cell(pooled[c]["found_rate"]["k"], pooled[c]["found_rate"]["n"], pooled[c]["found_rate"]["bootstrap95"]))
    add("found_right", "inter", "found_right", lambda c: cell(pooled[c]["found_right_level_rate"]["k"], pooled[c]["found_right_level_rate"]["n"], pooled[c]["found_right_level_rate"]["bootstrap95"]))
    for lvl in levels:
        add(f"fd_{lvl}", "inter", "fd_level", lambda c, lvl=lvl: cell(pooled[c]["levels_found"].get(lvl, 0), g(c, "gt_pairs")), params={"level": "ui.testing.s.lvl." + lvl})
    add("strict", "inter", "strict", lambda c: cell(g(c, "strict_silent_misses"), g(c, "gt_pairs")))
    add("unconf", "inter", "unconf", lambda c: cell(g(c, "unconfirmed"), g(c, "gt_pairs")))
    add("other", "inter", "other", lambda c: cell(sum(pooled[c]["other_outcomes"].values()), g(c, "gt_pairs")))
    add("false", "inter", "false", lambda c: cell(g(c, "false_alarms"), g(c, "found") + g(c, "false_alarms")))
    add("dup", "checks", "dup", lambda c: cell(g(c, "dup_groups_flagged"), g(c, "dup_gt_groups")))
    add("nondaily", "checks", "nondaily", lambda c: cell(g(c, "nondaily_flagged"), g(c, "nondaily_gt") - g(c, "nondaily_not_extracted")))
    add("eye_od", "checks", "eye_od", lambda c: cell(g(c, "eye_ambiguous_OD"), g(c, "eye_extracted")))
    add("eye_sched", "checks", "eye_sched", lambda c: cell(g(c, "eye_schedule_ready"), g(c, "eye_extracted")))
    add("unusual", "checks", "unusual", lambda c: cell(g(c, "unusual_doc_flagged"), m["conditions"][c]["by_category"]["unusual_strength"]["documents"]))
    add("garbled", "checks", "garbled", lambda c: cell(g(c, "garbled_flagged"), g(c, "garbled_gt") - g(c, "garbled_not_extracted")))
    add("garbled_ready", "checks", "garbled_ready", lambda c: cell(g(c, "garbled_interaction_ready"), g(c, "garbled_gt") - g(c, "garbled_not_extracted")))
    add("ov_equal", "overlay", "ov_equal", lambda c: cell(g(c, "ov_equal_to_gt_mode"), pooled[c]["documents"]))
    add("ov_newly", "overlay", "ov_newly", lambda c: cell(g(c, "ov_newly_found"), g(c, "unconfirmed")))
    add("ov_false", "overlay", "ov_false", lambda c: cell(g(c, "ov_false_alarms"), g(c, "ov_found_right_level") + g(c, "ov_false_alarms")))
    add("failed", "ops", "failed", lambda c: cell(len(m["conditions"][c]["failed"]), docs))
    gids = ["crit", "detect_raw", "detect_norm", "review", "inter", "checks", "overlay", "ops"]
    if {e["group"] for e in entries} != set(gids):
        raise SystemExit("stress groups out of sync")
    params = {"docs": docs, "conditions": len(conds), "readings": docs * len(conds), "meds": g(conds[0], "gt_meds"), "pairs": g(conds[0], "gt_pairs"),
              "failed": sum(len(m["conditions"][c]["failed"]) for c in conds), "running": env["ollama_version_running"], "pinned": env["ollama_version_pinned"], "level": 95}
    return {"run": True, "date": env["started"][:10], "source": SS_METRICS, "conditions": conds, "params": params, "groups": gids, "entries": entries,
            "also": {"doc": "docs/STRESS_RESULTS.md", "source": SS_METRICS, "per_doc": f"{SS}/per_document.csv"}}


def build() -> dict:
    n2, p3e, st, p4, live, form = (load(s) for s in (N2, P3E, STRESS, P4, LIVE, FORMULARY))
    verify_final_folder()
    entries: list[dict] = []

    def add(id, group, value, unit, source, measures, data, params, caveat=None, **extra):
        entries.append({"id": id, "group": group, "label": f"ui.testing.f.{id}", "value": value, "unit": unit, "source": source, "measures": f"ui.testing.m.{measures}",
                        "data": f"ui.testing.d.{data}", "params": params, "caveat": f"ui.testing.c.{caveat}" if caveat else None, "split": "dev", "date": RUN_DATES[source], **extra})

    d = lambda *k: dig(n2, *k, src=N2)  # noqa: E731
    docs, conds = d("raw", "all", "docs"), len(d("conditions")) - 1  # "all" is the pooled row
    per_cond = docs // conds
    dev_docs = {"docs": per_cond, "conditions": conds, "n": docs}
    assert dev_docs["docs"] * conds == docs, "pooled row is not documents x conditions"
    # 1 extraction, raw vs after the rules
    for key, which in (("raw", "as returned"), ("normalised", "after the rules")):
        suffix = "raw" if key == "raw" else "norm"
        add(f"ex_f1_{suffix}", "extraction", d(key, "all", "med_f1"), "ratio", N2, "f1", "dev_docs", dev_docs, "upper_bound" if key == "normalised" else "dev_tuned")
    for key in ("raw", "normalised"):
        suffix = "raw" if key == "raw" else "norm"
        add(f"ex_every_{suffix}", "extraction", d(key, "all", "med_fully_correct_rate"), "ratio", N2, "every_field", "dev_docs", dev_docs, "upper_bound" if key == "normalised" else "dev_tuned")
    # 2 invented values
    for key in ("raw", "normalised"):
        suffix = "raw" if key == "raw" else "norm"
        add(f"inv_{suffix}", "invented", d(key, "all", "invented_value_rate"), "ratio", N2, "invented", "dev_docs", dev_docs, "dev_tuned")
    # 3 flags (app mode: model output only, no document text)
    lv = d("review_levels_app", "all")
    meds = lv["name"]["medications"]
    add("fl_must", "flags", lv["name"]["share_must_confirm"], "ratio", N2, "must_confirm", "dev_meds", {**dev_docs, "meds": meds}, "flags_not_errors", n=lv["name"]["must_confirm"], of=meds)
    if lv["name"]["unflagged_errors"] != 0:
        raise SystemExit("the page text says no wrong medicine name reached the user unflagged; the metrics file says otherwise")
    add("fl_name", "flags", lv["name"]["unflagged_errors"], "count", N2, "name_unflagged", "dev_meds", {**dev_docs, "meds": meds}, None, n=lv["name"]["unflagged_errors"], of=lv["name"]["remaining_errors"])
    rd = d("readiness", "all")
    add("fl_identity", "flags", rd["wrong_resolved_generic"], "count", N2, "identity_wrong", "dev_meds", {**dev_docs, "meds": meds}, None, n=rd["wrong_resolved_generic"], of=rd["interaction_ready"])
    add("fl_timing", "flags", lv["timing"]["unflagged_errors"], "count", N2, "timing_unflagged", "dev_meds", {**dev_docs, "meds": meds}, "one_timing", n=lv["timing"]["unflagged_errors"], of=lv["timing"]["remaining_errors"])
    # 4 verification stack: the blind stress set
    for lang in ("en", "ta", "hi"):
        s = dig(st, lang, src=STRESS)
        fr, det = s["false_reject"], dig(s, "detection", "overall", src=STRESS)
        params = {"n": s["n"], "lang": lang}
        cav = "same_model" if lang == "en" else "small_unchecked"
        add(f"vf_{lang}_fr", "verification", fr["rate"], "ratio", STRESS, "false_reject", "stress", params, cav, n=fr["n"], of=fr["of"])
        add(f"vf_{lang}_det", "verification", det["combined"], "ratio", STRESS, "detected", "stress", params, cav, n=round(det["combined"] * det["n"]), of=det["n"])
    # 5 how many free-text lines are shown in the chosen language
    for lang in ("en", "ta", "hi"):
        pl = dig(p3e, "provenance_share", lang, "all", src=P3E)
        add(f"lg_{lang}", "language", pl["shown_in_language"], "ratio", P3E, "shown_in_language", "dev_lines", {"lines": pl["n"], "docs": dig(p3e, "documents", src=P3E)}, "varies", n=round(pl["shown_in_language"] * pl["n"]), of=pl["n"])
    # 6 safety layer
    sf = dig(p4, "safety", src=P4)
    gt = dig(p4, "ground_truth", src=P4)
    n_cond = len(dig(p4, "docs_by_condition", src=P4))
    pair_params = {"pairs": gt["pairs"], "found": gt["statuses"]["interaction_found"], "docs": dig(p4, "documents", src=P4), "conditions": n_cond}
    cov = [c for c in sf["silent_miss_cases"] if c["covered_by_flag"]]
    add("sf_silent", "safety", sf["silent_misses_not_covered_by_a_flag"], "count", P4, "silent_unflagged", "dev_pairs", pair_params, "partial_db", n=sf["silent_misses_not_covered_by_a_flag"], of=gt["statuses"]["interaction_found"] * n_cond)
    add("sf_strict", "safety", sf["silent_misses_strict"], "count", P4, "silent_strict", "dev_pairs", pair_params, "strict_covered", n=len(cov), of=gt["statuses"]["interaction_found"] * n_cond)
    add("sf_false", "safety", sf["false_alarms"], "count", P4, "false_alarm", "dev_pairs", pair_params, None, n=sf["false_alarms"], of=gt["pairs"] * n_cond)
    for cond in ("clean", "poor"):
        add(f"sf_nc_{cond}", "safety", dig(p4, "share_not_checked_by_condition", cond, src=P4), "ratio", P4, f"not_checked_{cond}", "dev_pairs", pair_params, "partial_db")
    # 7 live runs of the real app
    done = [r for r in live if r["after_delete"] == {"session": 401, "document": 401, "list": 401} and not r["console_errors"] and r["receipt"]]
    if len(done) != len(live):
        raise SystemExit(f"{LIVE}: a recorded flow did not finish cleanly; the page would claim otherwise")
    add("live_flows", "live", len(done), "count", LIVE, "live_flows", "live", {"n": len(live), "doc": live[0]["image"].split("/")[1].replace(".png", "")}, "live_not_perf", n=len(done), of=len(live))

    limits = {"formulary": len(dig(form, "medicines", src=FORMULARY)), "docs": per_cond, "conditions": conds}
    return {
        "_meta": {"script": "scripts/build_testing_page_data.py", "script_version": SCRIPT_VERSION, "sources": SOURCES, "dates": "commit date of each source file (RUN_DATES)",
                  "note": "Every figure on /how-we-tested-it is read from this file. Synthetic documents only."},
        "final_test": {"run": True, "source": FT_METRICS, "rule": "the 40-document test split was used once (final-test-v1); see docs/FINAL_TEST_RESULTS.md"},
        "test": test_section(),
        "stress_ext": stress_section(),
        "limits_params": limits,
        "groups": ["extraction", "invented", "flags", "verification", "language", "safety", "live"],
        "entries": entries,
    }


def render(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render(build())
    if a.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("up to date" if ok else "STALE: python scripts/build_testing_page_data.py")
        return 0 if ok else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
