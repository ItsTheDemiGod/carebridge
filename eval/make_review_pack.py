"""Build the native-speaker review pack from a Phase 3 dev run (synthetic content only, no model calls).
  python -m eval.make_review_pack [--run-id phase3-dev-clean]
Writes docs/review_pack/review_ta.html, review_hi.html (self-contained, UTF-8, no external resources) and review_ta.csv, review_hi.csv (UTF-8 with BOM).

Fixed selection of 10 dev documents (rule: one per case template, the first dev document of each, with the remaining two chosen so that
all three difficulty levels and both document types appear): 8 templates, clean/abbreviated/messy, 8 discharge summaries and 2 prescriptions.
"""

import argparse
import csv
import html
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACK = REPO / "docs" / "review_pack"
SELECTION = ["ds_006", "ds_008", "ds_011", "ds_018", "ds_023", "ds_025", "ds_037", "ds_040", "rx_003", "rx_016"]
LANG = {"ta": "Tamil", "hi": "Hindi"}
VERDICTS = "correct, understandable_but_awkward, wrong_meaning, unsafe"
COLUMNS = ["document_id", "line_id", "language", "source_text", "shown_text", "status", "provenance", "label", "reviewer_verdict", "reviewer_comment"]
CSS = ("body{font-family:system-ui,'Noto Sans Tamil','Noto Sans Devanagari',sans-serif;max-width:1100px;margin:1.5rem auto;padding:0 1rem;color:#1d2b2a}"
       "table{border-collapse:collapse;width:100%;margin:.5rem 0 2rem}td,th{border:1px solid #b9c4c2;padding:.4rem .6rem;vertical-align:top;font-size:.95rem}th{background:#e6eeec;text-align:left}"
       ".ok{color:#1b6b3a;font-weight:600}.bad{color:#9b2c1d;font-weight:600}.tpl{color:#44566a;font-weight:600}.rej{color:#777;font-style:italic}.sm{font-size:.85rem;color:#44566a}h2{margin-top:2rem}")


def rows_for(rec: dict, lang: str) -> list[dict]:
    out = []
    for sec in rec["explanation"]["sections"]:
        for ln in sec["lines"]:
            if ln["kind"] in ("disclaimer", "not_found"):
                continue
            t, en = ln["text"][lang], ln["text"]["en"]
            v = t["verification"]
            out.append(dict(document_id=rec["doc"], line_id=ln["line_id"], language=lang, kind=ln["kind"], source_text=ln["source_text"], english=en["text"], shown_text=t["text"],
                            status=t["status"], provenance=t.get("provenance", "template"), label=t.get("label_key") or "", verdict=v.get("judge_verdict"), reason=v.get("reason"), rejected=v["candidate"] if t["status"] in ("unverified",) else None,
                            back=v.get("back_translation"), notices=[n["text"][lang]["text"] for n in ln["notices"] if lang in n["text"]], flags=ln["flags"]))
    return out


def page(lang: str, data: list[tuple[dict, list[dict]]], meta: dict) -> str:
    e = html.escape
    h = [f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>CareBridge {LANG[lang]} review</title><style>{CSS}</style></head><body>",
         f"<h1>CareBridge: {LANG[lang]} review pack</h1><p>All content is synthetic (invented documents). Please judge only the <b>text shown to the user</b> (column 'Shown to user'). "
         f"For each row, choose a verdict in the CSV file: <b>{VERDICTS}</b>. Status: <span class='tpl'>template</span> = fixed sentence; <span class='ok'>verified</span> = automatic checks passed; "
         "<span class='bad'>unverified / original_only</span> = the automatic explanation was rejected, so the original English is shown with a notice. Rejected model text is greyed and is NOT shown to users; it is listed only so you can see why it failed. "
         "Provenance: <b>phrase_library</b> = a standard sentence from our phrase library (its text is reviewed separately in phrase_review_sheet.csv); <b>model_checked</b> = machine-written, checked by software only; <b>original_only</b> = original English; <b>template</b> = fixed sentence. Nothing here has been reviewed by a native speaker yet.</p>"]
    for rec, rows in data:
        h.append(f"<h2>{e(rec['doc'])} <span class='sm'>{e(meta[rec['doc']])}</span></h2><table><tr><th>Line</th><th>Extracted English</th><th>English explanation</th><th>Shown to user ({LANG[lang]})</th><th>Status</th><th>Provenance / label</th><th>Judge</th></tr>")
        for r in rows:
            cls = {"template": "tpl", "verified": "ok"}.get(r["status"], "bad")
            extra = ""
            if r["rejected"]:
                extra += f"<div class='rej'>Rejected model text: {e(r['rejected'])}</div>"
            if r["back"]:
                extra += f"<div class='sm'>Back-translation used by the checker: {e(r['back'])}</div>"
            if r["notices"]:
                extra += "".join(f"<div class='sm'>Notice: {e(n)}</div>" for n in r["notices"])
            judge = (e(r["verdict"] or "-") + (f"<div class='sm'>{e(r['reason'] or '')}</div>" if r["reason"] and r["status"] != "verified" else ""))
            h.append(f"<tr><td>{e(r['line_id'])}</td><td>{e(r['source_text'])}</td><td>{e(r['english'])}</td><td>{e(r['shown_text'])}{extra}</td><td class='{cls}'>{e(r['status'])}</td><td class='sm'>{e(r['provenance'])}<br>{e(r['label'])}</td><td>{judge}</td></tr>")
        h.append("</table>")
    return "".join(h) + "</body></html>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="phase3-dev-clean")
    a = ap.parse_args()
    manifest = {d["id"]: d for d in json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]}
    assert all(manifest[d]["split"] == "dev" for d in SELECTION), "review pack uses dev documents only"
    meta = {d: f"{manifest[d]['document_type']}, {manifest[d]['template']}, {manifest[d]['difficulty']}" for d in SELECTION}
    recs = [json.loads((REPO / "eval" / "runs" / a.run_id / "docs" / f"{d}.json").read_text(encoding="utf-8")) for d in SELECTION]
    PACK.mkdir(parents=True, exist_ok=True)
    for lang in LANG:
        data = [(r, rows_for(r, lang)) for r in recs]
        (PACK / f"review_{lang}.html").write_text(page(lang, data, meta), encoding="utf-8", newline="\n")
        with (PACK / f"review_{lang}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            for _, rows in data:
                w.writerows([{**r, "reviewer_verdict": "", "reviewer_comment": ""} for r in rows])
        print(lang, sum(len(r) for _, r in data), "rows")


if __name__ == "__main__":
    main()
