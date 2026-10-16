"""Schedule (suggested slots), user time overrides, adherence events and the doctor summary. Data only: no reminders are sent, no advice is given."""
from datetime import date as Date
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import Ctx, Sess, db_conn, get_ctx, get_document_or_404, require_consent
from app.api.errors import ApiError
from app.db import repo
from app.services import result as R
from app.services import schedule as S
from app.services import templates as T

router = APIRouter(prefix="/api/v1")
MAX_SUMMARY_DAYS = 62


class OverridesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overrides: dict[str, list[str]] = Field(default_factory=dict, max_length=40)


class AdherenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(max_length=64)
    med_ref: str = Field(max_length=4)
    scheduled_time: str = Field(max_length=5)
    date: str = Field(max_length=10)
    status: Literal["taken", "skipped"]


def parse_date(s: str) -> Date:
    try:
        if len(s) != 10:
            raise ValueError(s)
        return Date.fromisoformat(s)
    except ValueError:
        raise ApiError(422, "invalid_request")


def local_now() -> datetime:
    return datetime.now()  # server local time = the user's local time in this local-first prototype (tests replace this)


def med_name(c) -> str:
    return (T.display_name(c.med)[0] or c.med.resolved_generic or "").strip()


def build(ctx: Ctx, conn, doc_id: str, lang: str) -> dict:
    """Slots, per-medicine entries and the not-scheduled list for the current overlay and the stored time overrides."""
    _, ov, _ = R.load_overlay(ctx, conn, doc_id)
    over = repo.get_payload(conn, ctx.vault, doc_id, "schedule_overrides") or {}
    events: list[str] = []
    slots, meds, skipped, notices = [], [], [], set()
    for c in ov.meds:
        sug = S.suggest(c)
        user = over.get(c.ref) if (sug.times or sug.settable) else None  # overrides only for medicines that are schedule_ready
        times = user if user else sug.times
        f = c.med.frequency
        if not times:
            skipped.append({"ref": c.ref, "name": med_name(c), "reason": sug.reason, "template_id": f"schedule.not.{sug.reason}", "text": R.checked(f"schedule.not.{sug.reason}", lang, events),
                            "user_can_set_times": sug.settable})
            continue
        if sug.no_meal_timing and not user:
            notices.add("schedule.no_meal_timing")
        days = c.med.duration_days.value
        meds.append({"ref": c.ref, "name": med_name(c), "strength": c.med.strength, "dose": c.med.dose, "times_per_day": f.times_per_day.value, "timing_label": f.timing_label.value,
                     "times": times, "source": "user" if user else "suggested", "duration_days": days if isinstance(days, int) else None,
                     "duration_text": R.checked("schedule.duration_days", lang, events, n=days) if isinstance(days, int) and days >= 1 else None})
        slots += [{"med_ref": c.ref, "name": med_name(c), "time": t, "source": "user" if user else "suggested"} for t in times]
    slots.sort(key=lambda x: (x["time"], x["med_ref"]))
    return {"document_id": doc_id, "language": lang, "notice": {"template_id": "schedule.notice", "text": R.checked("schedule.notice", lang, events)},
            "extra_notices": [{"template_id": t, "text": R.checked(t, lang, events)} for t in sorted(notices)], "slots": slots, "medicines": meds, "not_scheduled": skipped,
            "guardrail_events": events}


def slot_set(sched: dict) -> set[tuple[str, str]]:
    return {(s["med_ref"], s["time"]) for s in sched["slots"]}


@router.get("/documents/{doc_id}/schedule")
def get_schedule(doc_id: str, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "awaiting_confirmation":
        raise ApiError(409, "not_ready")
    return build(ctx, conn, doc_id, s.language)


@router.put("/documents/{doc_id}/schedule-overrides")
def put_overrides(doc_id: str, body: OverridesIn, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Replaces the whole set. Times are HH:MM, at most 6 per medicine. Only medicines that can be scheduled accept times."""
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "awaiting_confirmation":
        raise ApiError(409, "not_ready")
    _, ov, _ = R.load_overlay(ctx, conn, doc_id)
    eligible = {c.ref for c in ov.meds if (sg := S.suggest(c)).times or sg.settable}
    clean = {}
    for ref, times in body.overrides.items():
        if ref not in eligible or not S.valid_times(times):
            raise ApiError(422, "invalid_request")
        clean[ref] = sorted(times)
    repo.put_payload(conn, ctx.vault, doc_id, "schedule_overrides", clean)
    return build(ctx, conn, doc_id, s.language)


# --- adherence --------------------------------------------------------------------------------------------------------------------------------
@router.post("/adherence", status_code=201)
def log_adherence(body: AdherenceIn, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    get_document_or_404(conn, s, body.document_id)
    day = parse_date(body.date)
    if not S.REF.match(body.med_ref) or not S.HHMM.match(body.scheduled_time) or abs((day - local_now().date()).days) > 400:
        raise ApiError(422, "invalid_request")
    if (body.med_ref, body.scheduled_time) not in slot_set(build(ctx, conn, body.document_id, s.language)):
        raise ApiError(422, "invalid_request")  # only an existing slot of a scheduled medicine can be logged
    eid = repo.put_adherence(conn, s.id, body.document_id, body.med_ref, body.scheduled_time, body.date, body.status)
    return {"id": eid, "document_id": body.document_id, "med_ref": body.med_ref, "scheduled_time": body.scheduled_time, "date": body.date, "status": body.status}


@router.get("/adherence")
def list_adherence(document_id: str = Query(max_length=64), date_from: str | None = Query(None, alias="from", max_length=10), date_to: str | None = Query(None, alias="to", max_length=10),
                   s: Sess = Depends(require_consent), conn=Depends(db_conn)):
    get_document_or_404(conn, s, document_id)
    for x in (date_from, date_to):
        if x:
            parse_date(x)
    return {"events": repo.list_adherence(conn, s.id, document_id, date_from, date_to)}


@router.delete("/adherence/{event_id}", status_code=204)
def delete_adherence(event_id: str, s: Sess = Depends(require_consent), conn=Depends(db_conn)):
    if not repo.delete_adherence(conn, s.id, event_id):
        raise ApiError(404, "not_found")
    return Response(status_code=204)


# --- doctor summary ---------------------------------------------------------------------------------------------------------------------------
@router.get("/documents/{doc_id}/doctor-summary")
def doctor_summary(doc_id: str, date_from: str | None = Query(None, alias="from", max_length=10), date_to: str | None = Query(None, alias="to", max_length=10),
                   s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """A plain list for the user to show a doctor: confirmed medicines with strength and schedule, taken / skipped / missed counts, what is still unconfirmed,
    and the interaction lines exactly as the user sees them. Counts only: no percentages, no scores, no advice."""
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "awaiting_confirmation":
        raise ApiError(409, "not_ready")
    lang = s.language
    all_events = repo.list_adherence(conn, s.id, doc_id)
    now = local_now()
    today = now.date()
    start = parse_date(date_from) if date_from else (Date.fromisoformat(min(e["date"] for e in all_events)) if all_events else today)
    end = parse_date(date_to) if date_to else (Date.fromisoformat(max(e["date"] for e in all_events)) if all_events else today)
    if end < start or (end - start).days > MAX_SUMMARY_DAYS:
        raise ApiError(422, "invalid_request")
    events = [e for e in all_events if start.isoformat() <= e["date"] <= end.isoformat()]
    sched = build(ctx, conn, doc_id, lang)
    days = [start + timedelta(n) for n in range((min(end, today) - start).days + 1)] if start <= today else []
    logged = {(e["med_ref"], e["scheduled_time"], e["date"]): e["status"] for e in events}
    out = []
    for m in sched["medicines"]:
        taken = sum(1 for e in events if e["med_ref"] == m["ref"] and e["status"] == "taken")
        skipped = sum(1 for e in events if e["med_ref"] == m["ref"] and e["status"] == "skipped")
        missed = sum(1 for dd in days for t in m["times"] if (dd < today or t <= now.strftime("%H:%M")) and (m["ref"], t, dd.isoformat()) not in logged)  # a slot later today is not missed yet
        out.append({**{k: m[k] for k in ("ref", "name", "strength", "dose", "times_per_day", "timing_label", "times", "duration_days", "duration_text")}, "taken": taken, "skipped": skipped, "missed": missed})
    res = R.assemble(ctx, conn, d, lang)
    events_g = list(res["guardrail_events"])
    unconfirmed = []
    _, ov, _ = R.load_overlay(ctx, conn, doc_id)
    for c in ov.meds:
        if c.unresolved:
            unconfirmed.append({"ref": c.ref, "name": med_name(c), "reasons": [{"id": r, "text": T.render(f"confirm.flag.{r}", lang) if f"confirm.flag.{r}" in T.load()["strings"] else None} for r in c.unresolved]})
    safety = next((sec["lines"] for sec in res["explanation"]["sections"] if sec["id"] == "safety"), [])
    found = [p for p in (res["explanation"]["safety"] or {}).get("pair_results", []) if p["status"] == "interaction_found"]
    H = lambda k: R.checked(k, lang, events_g)  # noqa: E731
    return {"document_id": doc_id, "language": lang, "title": H("summary.title"), "period": {"from": start.isoformat(), "to": end.isoformat()},
            "headings": {k: H(f"summary.heading.{k}") for k in ("medicines", "adherence", "unconfirmed", "interactions")},
            "labels": {k: H(f"summary.label.{k}") for k in ("taken", "skipped", "missed")},
            "medicines": out, "unconfirmed": unconfirmed, "not_scheduled": sched["not_scheduled"],
            "interactions": {"lines": [ln["text"][lang]["text"] for ln in safety], "found": [{"a": p["a"], "b": p["b"], "generic_a": p["generic_a"], "generic_b": p["generic_b"], "level": p["level"]} for p in found]},
            "schedule_notice": sched["notice"]["text"], "disclaimer": H("summary.disclaimer"), "guardrail_events": events_g}
