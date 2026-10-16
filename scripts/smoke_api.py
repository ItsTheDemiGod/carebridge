"""Live smoke test of the whole API flow with the REAL local model (Ollama). Dev split, synthetic rendered images only.

  1. start the API:   cd backend; .venv\\Scripts\\uvicorn app.main:app          (needs CAREBRIDGE_DATA_KEY: python scripts/generate_data_key.py)
  2. run:             backend\\.venv\\Scripts\\python scripts/smoke_api.py [--base http://127.0.0.1:8000] [--doc ds_037] [--conditions clean,poor]

Flow per image: session (Tamil) -> consent -> upload -> poll states -> medicines -> confirmations (the smoke script may use GROUND-TRUTH drug names to pick
formulary entries; this is only for the smoke test) -> result en + ta -> schedule -> two adherence events -> doctor summary -> delete session -> verify the
database holds no rows for that session. Prints timings, states and at most 3 short sample lines (never whole texts)."""
import argparse
import hashlib
import json
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
from app.config import settings  # noqa: E402

HEADERS = {"X-CareBridge-Request": "1"}
TABLES = (("sessions", "id"), ("consents", "session_id"), ("documents", "session_id"), ("adherence_events", "session_id"))


def short(s: str, n: int = 110) -> str:
    return (s[:n] + "...") if len(s) > n else s


def check_dev(doc: str) -> None:
    m = {d["id"]: d for d in json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]}
    if doc not in m or m[doc]["split"] != "dev":
        raise SystemExit(f"{doc} is not a dev document: the test split is never used before Phase 7")


def ground_truth(doc: str) -> list[dict]:
    return json.loads((REPO / "data" / "ground_truth" / f"{doc}.json").read_text(encoding="utf-8"))["medications"]


def session_id_for(token: str) -> str | None:
    c = sqlite3.connect(f"file:{settings.db_file}?mode=ro", uri=True)
    try:
        r = c.execute("SELECT id FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        return r[0] if r else None
    finally:
        c.close()


def rows_for(sid: str) -> dict:
    c = sqlite3.connect(f"file:{settings.db_file}?mode=ro", uri=True)
    try:
        out = {t: c.execute(f"SELECT COUNT(*) FROM {t} WHERE {col}=?", (sid,)).fetchone()[0] for t, col in TABLES}
        out["payloads"] = c.execute("SELECT COUNT(*) FROM payloads WHERE document_id IN (SELECT id FROM documents WHERE session_id=?)", (sid,)).fetchone()[0]
        return out
    finally:
        c.close()


def pick_formulary(cl: httpx.Client, gt: dict) -> tuple[str | None, str]:
    name = gt.get("generic_name") or gt.get("brand_name") or ""
    for q in (gt.get("generic_name"), gt.get("brand_name")):
        if not q:
            continue
        res = cl.get("/api/v1/formulary/search", params={"q": q.split()[0], "limit": 5}).json()["results"]
        for e in res:
            names = [e["generic"].lower()] + [b.lower() for b in e["brand_names"]]
            if q.lower() in names:
                strength = gt.get("strength") if gt.get("strength") in e["available_strengths"] else "as_on_my_label"
                return e["id"], strength
    return None, "as_on_my_label"


def run(base: str, doc: str, condition: str) -> dict:
    img = REPO / "data" / "rendered" / condition / f"{doc}.png"
    if not img.exists():
        raise SystemExit(f"missing {img}: run  python data/render_documents.py  first")
    rep: dict = {"doc": doc, "condition": condition, "states": []}
    gt = ground_truth(doc)
    with httpx.Client(base_url=base, headers=HEADERS, timeout=60) as cl:
        assert cl.post("/api/v1/sessions", json={"language": "ta"}).status_code in (200, 201)
        token = cl.cookies.get("cb_session")
        sid = session_id_for(token)
        notice = cl.get("/api/v1/consent-notice", params={"lang": "ta"}).json()
        r = cl.post("/api/v1/consent", json={"notice_version": notice["version"], "purposes": ["process_photo", "store_results_for_session"]})
        assert r.status_code == 200, r.text
        t0 = time.time()
        r = cl.post("/api/v1/documents", content=img.read_bytes(), headers={"Content-Type": "image/png"})
        assert r.status_code == 202, r.text
        did = r.json()["id"]
        seen, t_ac, snap_ac, last = [], None, None, None
        t_ready = {}
        while time.time() - t0 < 900:
            d = cl.get(f"/api/v1/documents/{did}").json()
            key = (d["state"], json.dumps(d["narrative"], sort_keys=True))
            if key != last:
                last = key
                rep["states"].append({"t": round(time.time() - t0, 1), "state": d["state"], "narrative": d["narrative"]})
            if d["state"] == "awaiting_confirmation" and t_ac is None:
                t_ac, snap_ac = time.time() - t0, dict(d["narrative"])
                break
            if d["state"] == "failed":
                rep["failed"] = d["error_code"]
                return rep
            time.sleep(2)
        rep["t_awaiting_confirmation_s"], rep["narrative_at_that_moment"] = round(t_ac, 1), snap_ac
        # the user confirms the medicines now, while the narrative is (probably) still running in the background
        meds = cl.get(f"/api/v1/documents/{did}/medicines").json()["medicines"]
        decisions = []
        for m in meds:
            i = m["index"]
            g = gt[i] if i < len(gt) else None
            acks = [x["id"] for x in m["reasons"] if x["kind"] == "acknowledge"]
            if m["review_level"] != "must_confirm" or not g:
                continue
            if any(x["kind"] == "name" for x in m["reasons"]):
                fid, strength = pick_formulary(cl, g)
                decisions.append({"index": i, "action": "select_formulary_drug", "formulary_id": fid, "strength_choice": strength, "acknowledged_flags": acks} if fid
                                 else {"index": i, "action": "not_in_list"})
            else:
                decisions.append({"index": i, "action": "confirm_as_extracted", "acknowledged_flags": acks})
        rep["medicines"] = {"extracted": len(meds), "ground_truth": len(gt), "must_confirm": sum(m["review_level"] == "must_confirm" for m in meds),
                            "name_reasons": sum(any(x["kind"] == "name" for x in m["reasons"]) for m in meds), "decisions": [x["action"] for x in decisions]}
        before = cl.get(f"/api/v1/documents/{did}/result", params={"lang": "en"}).json()
        rep["before_confirmation"] = {"confirm_first": before["confirm_first"], "pairs": _pairs(before)}
        t_conf = time.time() - t0
        r = cl.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": decisions})
        assert r.status_code == 200, r.text
        rep["t_confirmation_sent_s"] = round(t_conf, 1)
        # wait for the narrative of every requested language
        while time.time() - t0 < 900:
            d = cl.get(f"/api/v1/documents/{did}").json()
            for lang, st in d["narrative"].items():
                if st in ("ready", "failed") and lang not in t_ready:
                    t_ready[lang] = {"state": st, "t_s": round(time.time() - t0, 1)}
            if len(t_ready) == len(d["narrative"]):
                break
            time.sleep(2)
        rep["timings_server"] = d["timings"]
        rep["narrative_done"] = t_ready
        rep["narrative_finished_before_confirmation_sent"] = {k: v["t_s"] <= t_conf for k, v in t_ready.items()}
        res = {lang: cl.get(f"/api/v1/documents/{did}/result", params={"lang": lang}).json() for lang in ("en", "ta")}
        rep["after_confirmation"] = {"confirm_first": res["en"]["confirm_first"], "pairs": _pairs(res["en"]), "narrative_status": res["en"]["narrative_status"]}
        rep["lines"] = {lang: _line_stats(r_) for lang, r_ in res.items()}
        sample = [ln for s in res["en"]["explanation"]["sections"] for ln in s["lines"] if ln["kind"] in ("advice", "follow_up", "warning")][:3]
        rep["sample_lines"] = [short(ln["text"]["en"]["text"]) for ln in sample]
        sc = cl.get(f"/api/v1/documents/{did}/schedule").json()
        rep["schedule"] = {"slots": len(sc["slots"]), "not_scheduled": {x["ref"]: x["reason"] for x in sc["not_scheduled"]}}
        logged = 0
        for slot in sc["slots"][:2]:
            logged += cl.post("/api/v1/adherence", json={"document_id": did, "med_ref": slot["med_ref"], "scheduled_time": slot["time"], "date": date.today().isoformat(), "status": "taken"}).status_code == 201
        sm = cl.get(f"/api/v1/documents/{did}/doctor-summary").json()
        rep["adherence_logged"], rep["summary"] = logged, {"medicines": len(sm["medicines"]), "unconfirmed": len(sm["unconfirmed"]), "taken": sum(m["taken"] for m in sm["medicines"])}
        rep["total_s"] = round(time.time() - t0, 1)
        before_rows = rows_for(sid)
        r = cl.delete("/api/v1/session")
        assert r.status_code == 200
        rep["rows_before_delete"], rep["rows_after_delete"], rep["receipt"] = before_rows, rows_for(sid), r.json()["deleted"]
        assert not any(rep["rows_after_delete"].values()), "rows remain after deletion"
    return rep


def _pairs(res: dict) -> dict:
    out: dict = {}
    for p in res["explanation"]["safety"]["pair_results"]:
        out[p["status"]] = out.get(p["status"], 0) + 1
    return out


def _line_stats(res: dict) -> dict:
    stats: dict = {}
    for s in res["explanation"]["sections"]:
        if s["id"] in ("follow_ups", "advice", "warnings"):
            for ln in s["lines"]:
                t = next(iter(ln["text"].values()))
                k = "phrase_library" if ln["provenance"] == "phrase_library" else t["provenance"] if not ln["narrative_pending"] else "pending"
                stats[k] = stats.get(k, 0) + 1
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--doc", default="ds_037")
    ap.add_argument("--conditions", default="clean,poor")
    a = ap.parse_args()
    check_dev(a.doc)
    for cond in a.conditions.split(","):
        print(json.dumps(run(a.base, a.doc, cond), ensure_ascii=False, indent=1))
