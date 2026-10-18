"""Phase 6d: writes frontend/src/data/testing.generated.json, the figures of the "How we tested it" page.   python scripts/build_testing_page_data.py [--check]

Reads ONLY small committed files (listed in SOURCES and in docs/TESTING_PAGE.md); every number on the page comes from here, none is typed into a string
(strings carry {placeholders} that are filled from each entry's params). Fails loudly when a file, key or expected property is missing. No model, no network.
Each entry: id, group, label (string id), value, unit (ratio | count), source (committed file), measures (string id), data (string id) + params, caveat (string id or null),
split (dev | test), date (the day the source file was committed; the metrics files carry no date of their own, see RUN_DATES), plus optional n/of for "k of n" figures.
The held-out TEST split has not been run: `final_test.run` is false and the builder refuses to build if eval/test_runs.log exists, so Phase 7 must extend this script
(add the test figures, set run to true) instead of leaving a stale "not yet run" on the page. --check compares with the committed file (staleness test)."""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "frontend" / "src" / "data" / "testing.generated.json"
TEST_LOG = REPO / "eval" / "test_runs.log"  # written by any run on the held-out test split (--final-test-run)
SCRIPT_VERSION = "1"

N2 = "eval/results/dev-ollama-v1-normalised-v2/metrics.json"  # Phase 2 raw output re-scored with the rules (2h/2i), 20 dev documents x 5 image conditions
P3E = "eval/results/phase3e-dev-clean/metrics.json"  # Phase 3e: free-text lines shown per language (dev, clean images)
STRESS = "eval/results/stress-v1/metrics.json"  # Phase 3e blind stress set (authored correct and wrong lines)
P4 = "eval/results/phase4-dev-with-supplement/metrics.json"  # Phase 4 safety layer with the author-checked supplement enabled
LIVE = "docs/smoke/phase6c_live.json"  # Phase 6c: three end-to-end runs of the real app (JSON lines)
FORMULARY = "data/reference/formulary.json"
SOURCES = [N2, P3E, STRESS, P4, LIVE, FORMULARY]
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


def build() -> dict:
    n2, p3e, st, p4, live, form = (load(s) for s in (N2, P3E, STRESS, P4, LIVE, FORMULARY))
    if TEST_LOG.exists():
        raise SystemExit("eval/test_runs.log exists: a held-out test run was logged. Extend this script with the test figures (see docstring) before rebuilding.")
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
        "final_test": {"run": False, "source": "eval/test_runs.log", "rule": "the 40-document test split is used once, in Phase 7"},
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
