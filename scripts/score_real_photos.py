"""Score the real-photo test (Phase 7c; written and tested with mocks in 7a).   backend\\.venv\\Scripts\\python scripts\\score_real_photos.py [--base-url http://localhost:8000]

For every photo in data/real_photos/ named RPn_X.jpg (X = condition A to E) it drives the REAL app path through the API: session, consent for the CURRENT notice version,
raw-body upload, polling until awaiting_confirmation, the medicines endpoint; then DELETE /session. It compares the app's medicines (final values, after normalisation)
with the ground truth of the mapped synthetic document (data/real_photos/mapping.json) using the same scorer as the other evaluations (eval/matching.py).
It REFUSES to upload any file that is not RPn_X.jpg with RPn in the mapping and X in A..E. It prints only ids and counts; photos and raw outputs stay out of git.
Results: eval/results/real-photos-v1/{metrics.json, metrics.md, comparison.md} (aggregated). The real-photo metrics are compared with the RENDERED scan/photo/poor
conditions of the committed DEV results (never the test split). Needs the backend on port 8000 and the local model (Phase 7c)."""
import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from eval.final_test.stats import bootstrap_ci, wilson  # noqa: E402
from eval.matching import MED_FIELDS, NAME_THRESHOLD, field_value, med_similarity, one_to_one, score_document, summarize  # noqa: E402

CONDITIONS = "ABCDE"
CONDITION_NAMES = {"A": "daylight by a window", "B": "room lamp at night", "C": "partial shadow", "D": "tilted 15 to 20 degrees", "E": "crumpled or curved page"}
PHOTO = re.compile(r"^(RP\d+)_([A-E])\.jpe?g$", re.I)
DEV_REF = "eval/results/dev-ollama-v1-normalised-v2/metrics.json"
POLL_SECONDS, POLL_TIMEOUT = 5, 600


class Refusal(SystemExit):
    pass


def list_photos(folder: Path, mapping: dict) -> list[tuple[str, str, Path]]:
    """(sample, condition, path) for every acceptable photo; any other file stops the run (nothing is uploaded)."""
    bad, ok = [], []
    for p in sorted(folder.iterdir()):
        if p.name == "mapping.json" or p.is_dir():
            continue
        m = PHOTO.match(p.name)
        if not m or m.group(1).upper() not in mapping:
            bad.append(p.name)
        else:
            ok.append((m.group(1).upper(), m.group(2).upper(), p))
    if bad:
        raise Refusal(f"refusing to upload: {len(bad)} file(s) are not listed in the mapping or not named RPn_X.jpg: {bad[:10]}")
    return ok


def prediction_from_api(doc_type, meds: list[dict]) -> ExtractionOutput:
    out = []
    for m in meds:
        f = m["frequency"]
        out.append({"brand_name": m["as_written"].get("brand"), "generic_name": m["as_written"].get("generic"), "strength": m.get("strength"), "form": m.get("form") or "other",
                    "route": m.get("route") or "other", "dose": m.get("dose"),
                    "frequency": {"times_per_day": f.get("times_per_day"), "timing_label": f.get("timing_label") or "unspecified", "original_abbreviation": f.get("original_abbreviation"), "is_prn": bool(f.get("is_prn"))},
                    "duration_days": m.get("duration_days"), "duration_text": m.get("duration_text"), "special_instructions": None, "source_quote": m.get("source_quote") or "", "confidence": "high"})
    return ExtractionOutput.model_validate({"document_type": doc_type, "medications": out})


def run_photo(client, path: Path, language="en", timeout=POLL_TIMEOUT, sleep=POLL_SECONDS) -> tuple[dict | None, str | None]:
    """One photo through the real API. -> (medicines response or None, failure reason). Always ends with DELETE /session."""
    try:
        r = client.post("/api/v1/sessions", json={"language": language})
        if r.status_code not in (200, 201):
            return None, f"session_{r.status_code}"
        notice = client.get(f"/api/v1/consent-notice?lang={language}").json()
        r = client.post("/api/v1/consent", json={"notice_version": notice["version"], "purposes": ["process_photo", "store_results_for_session"]})
        if r.status_code != 200:
            return None, f"consent_{r.status_code}"
        r = client.post("/api/v1/documents", content=path.read_bytes(), headers={"Content-Type": "image/jpeg"})
        if r.status_code != 202:
            return None, f"upload_{r.status_code}_{(r.json().get('error') or {}).get('code', '')}"
        doc_id = r.json()["id"]
        t0 = time.time()
        while True:
            d = client.get(f"/api/v1/documents/{doc_id}").json()
            if d["state"] == "awaiting_confirmation":
                return client.get(f"/api/v1/documents/{doc_id}/medicines").json(), None
            if d["state"] == "failed":
                return None, f"failed_{d.get('error_code')}"
            if time.time() - t0 > timeout:
                return None, "poll_timeout"
            time.sleep(sleep)
    finally:
        client.delete("/api/v1/session")


def score_one(gt_doc: ExtractedDocument, text: str, meds_response: dict):
    gt = from_ground_truth(gt_doc)
    pred = prediction_from_api(gt.document_type, meds_response["medicines"])
    counters = score_document(gt, pred, text)
    G, P = gt.medications, pred.medications
    pairs = {j: i for i, j in one_to_one(len(G), len(P), lambda i, j: med_similarity(G[i], P[j]), NAME_THRESHOLD)}
    recs = []
    for j, m in enumerate(meds_response["medicines"]):
        i = pairs.get(j)
        bad = [f for f in MED_FIELDS if i is None or field_value(G[i], f) != field_value(P[j], f)] if i is not None else ["unpaired"]
        recs.append(dict(level=m["review_level"], name_err=i is None or any(x in bad for x in ("brand_name", "generic_name")), interaction_ready=m["interaction_ready"], schedule_ready=m["schedule_ready"]))
    return counters, recs


def aggregate(results: list[dict], skipped: list[dict]) -> dict:
    """results: [{sample, cond, counters, recs}] -> per condition and pooled metrics with Wilson and bootstrap intervals."""
    out = {}
    for cond in (*CONDITIONS, "all"):
        rows = [r for r in results if cond == "all" or r["cond"] == cond]
        if not rows:
            continue
        c = Counter()
        for r in rows:
            c += r["counters"]
        s = summarize(c)
        recs = [x for r in rows for x in r["recs"]]
        w = lambda k, n: None if not n else [round(v, 4) for v in wilson(k, n)]  # noqa: E731
        s["intervals"] = {"med_precision": w(c["med_tp"], c["med_tp"] + c["med_fp"]), "med_recall": w(c["med_tp"], c["med_tp"] + c["med_fn"]),
                          "med_f1_bootstrap": [round(v, 4) for v in b] if (b := bootstrap_ci([r["counters"] for r in rows], lambda x: summarize(x)["med_f1"])) else None,
                          "med_fully_correct_rate": w(c["med_fully_correct"], c["med_tp"])}
        s["photos_scored"] = len(rows)
        s["photos_skipped"] = sum(1 for k in skipped if cond == "all" or k["cond"] == cond)
        s["medicines"] = len(recs)
        s["must_confirm"] = sum(x["level"] == "must_confirm" for x in recs)
        s["share_must_confirm"] = round(s["must_confirm"] / len(recs), 4) if recs else None
        s["name_errors"] = sum(x["name_err"] for x in recs)
        s["name_errors_unflagged"] = sum(x["name_err"] and x["level"] == "none" for x in recs)
        s["interaction_ready"] = sum(x["interaction_ready"] for x in recs)
        out[cond] = s
    return out


def comparison(real: dict, root: Path = REPO) -> list[dict]:
    """Real-photo metrics (pooled) next to the RENDERED scan, photo and poor conditions of the committed DEV results (normalised)."""
    dev = json.loads((root / DEV_REF).read_text(encoding="utf-8"))["normalised"]
    rows = []
    for key, label in (("med_f1", "medicine F1"), ("med_fully_correct_rate", "fully-correct medicine rate"), ("invented_value_rate", "invented-value rate")):
        rows.append({"metric": label, "real photos (pooled)": real.get("all", {}).get(key), **{f"dev rendered {c}": dev[c].get(key) for c in ("scan", "photo", "poor")}})
    return rows


def markdown(m: dict) -> str:
    out = ["# Real-photo test (synthetic documents, printed and photographed with a phone)\n", "Aggregated counts only. Proportions: Wilson 95% intervals; F1: photo-level bootstrap interval. Very small samples: read the intervals.\n",
           "| condition | photos scored | skipped | precision | recall | F1 [bootstrap] | fully correct | medicines | must_confirm | name errors (unflagged) |", "|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "-" if x is None else f"{x:.3f}"  # noqa: E731
    ci = lambda i: "" if not i else f" [{i[0]:.2f}, {i[1]:.2f}]"  # noqa: E731
    for c, s in m["by_condition"].items():
        name = f"{c} ({CONDITION_NAMES[c]})" if c in CONDITION_NAMES else "all"
        i = s["intervals"]
        out.append(f"| {name} | {s['photos_scored']} | {s['photos_skipped']} | {f(s['med_precision'])}{ci(i['med_precision'])} | {f(s['med_recall'])}{ci(i['med_recall'])} | {f(s['med_f1'])}{ci(i['med_f1_bootstrap'])} | {f(s['med_fully_correct_rate'])}{ci(i['med_fully_correct_rate'])} | {s['medicines']} | {s['must_confirm']} | {s['name_errors']} ({s['name_errors_unflagged']}) |")
    if m["skipped"]:
        out += ["", "Skipped or failed uploads (listed, never dropped):", *[f"- {k['sample']}_{k['cond']}: {k['reason']}" for k in m["skipped"]]]
    return "\n".join(out) + "\n"


def comparison_markdown(rows: list[dict]) -> str:
    cols = list(rows[0])
    return "# Real photos versus rendered conditions (committed DEV results, normalised)\n\nThe gap between the real-photo column and the rendered columns measures how far the rendered images are from real phone photos.\n\n" + "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n" + "\n".join("| " + " | ".join("-" if r[c] is None else (f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c])) for c in cols) + " |" for r in rows) + "\n"


def run(client, folder: Path, root: Path = REPO, out_dir: Path | None = None, sleep=POLL_SECONDS) -> dict:
    mapping = json.loads((folder / "mapping.json").read_text(encoding="utf-8"))
    photos = list_photos(folder, mapping)
    if not photos:
        raise Refusal("no photos found in the folder")
    results, skipped = [], []
    for sample, cond, path in photos:
        entry = mapping[sample]
        resp, why = run_photo(client, path, sleep=sleep)
        print(f"{sample}_{cond}: {'ok' if resp else 'skipped ' + str(why)}")
        if resp is None:
            skipped.append({"sample": sample, "cond": cond, "reason": why})
            continue
        gt = ExtractedDocument.model_validate_json((root / entry["ground_truth"]).read_text(encoding="utf-8"))
        counters, recs = score_one(gt, (root / entry["text"]).read_text(encoding="utf-8"), resp)
        results.append({"sample": sample, "cond": cond, "counters": counters, "recs": recs})
    m = {"run_id": "real-photos-v1", "photos_found": len(photos), "by_condition": aggregate(results, skipped), "skipped": skipped,
         "note": "documents are synthetic; photos were taken by the project owner; the 'poor/photo/scan' rendered conditions are simulations of such photos"}
    m["comparison_with_dev_rendered"] = comparison(m["by_condition"])  # dev reference: the committed dev results of this repository
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "metrics.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8", newline="\n")
        (out_dir / "metrics.md").write_text(markdown(m), encoding="utf-8", newline="\n")
        (out_dir / "comparison.md").write_text(comparison_markdown(m["comparison_with_dev_rendered"]), encoding="utf-8", newline="\n")
    return m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    a = ap.parse_args(argv)
    import httpx
    with httpx.Client(base_url=a.base_url, headers={"X-CareBridge-Request": "1"}, timeout=60) as client:
        m = run(client, REPO / "data" / "real_photos", out_dir=REPO / "eval" / "results" / "real-photos-v1")
    print(f"scored {sum(s['photos_scored'] for c, s in m['by_condition'].items() if c != 'all')} photos, skipped {len(m['skipped'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
