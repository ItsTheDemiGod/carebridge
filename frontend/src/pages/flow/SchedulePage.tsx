import { useCallback, useEffect, useMemo, useState } from 'react'
import { deleteAdherence, getSchedule, listAdherence, logAdherence, saveOverrides } from '../../api/endpoints'
import { isAbort, type Problem } from '../../api/errors'
import type { AdherenceEvent, ScheduleResponse } from '../../api/types'
import { Button, ButtonLink } from '../../components/Button'
import { Notice } from '../../components/Badges'
import { Icon } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { DemoMarksNote } from '../../demo/DemoBar'
import { useDocId, useDocPath } from '../../demo/useDemo'
import { useT } from '../../i18n/I18n'
import { addDays, localDate, nextDose, validTimes } from '../../lib/time'

export function SchedulePage() {
  const id = useDocId()
  return (
    <FlowPage titleKey="ui.title.schedule" narrow={false}>
      <Schedule id={id} />
    </FlowPage>
  )
}

function Schedule({ id }: { id: string }) {
  const docPath = useDocPath()
  const { t, lang } = useT()
  const flow = useFlow()
  const sessionLang = flow.state.sessionLang
  const [data, setData] = useState<ScheduleResponse | null>(null)
  const [events, setEvents] = useState<AdherenceEvent[]>([])
  const [problem, setProblem] = useState<Problem | null>(null)
  const [day, setDay] = useState(() => localDate(new Date()))
  const [now, setNow] = useState(() => new Date())
  const [busy, setBusy] = useState<string | null>(null)
  const today = localDate(now)

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const [s, e] = await Promise.all([getSchedule(id, signal), listAdherence(id, localDate(addDays(new Date(), -7)), localDate(addDays(new Date(), 7)), signal)])
      setData(s)
      setEvents(e.events)
      setProblem(null)
    } catch (e) {
      if (!isAbort(e)) setProblem(flow.report(e))
    }
  }, [id, flow])

  useEffect(() => {
    if (!sessionLang) return
    const ctl = new AbortController()
    void load(ctl.signal)
    return () => ctl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, sessionLang])

  // the only timer on this page: refresh the "next dose" label while the page is open
  useEffect(() => {
    const h = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(h)
  }, [])

  const slots = data?.slots ?? []
  const ev = useMemo(() => new Map(events.map((e) => [`${e.med_ref}|${e.scheduled_time}|${e.date}`, e])), [events])
  const evFor = (ref: string, time: string, date = day) => ev.get(`${ref}|${time}|${date}`)

  const mark = async (slot: { med_ref: string; time: string }, status: 'taken' | 'skipped') => {
    const key = `${slot.med_ref}|${slot.time}`
    setBusy(key)
    setProblem(null)
    try {
      const old = evFor(slot.med_ref, slot.time)
      if (old) {
        await deleteAdherence(old.id)
        setEvents((x) => x.filter((e) => e.id !== old.id))
      }
      if (!old || old.status !== status) {
        const created = await logAdherence({ document_id: id, med_ref: slot.med_ref, scheduled_time: slot.time, date: day, status })
        setEvents((x) => [...x, created])
      }
    } catch (e) {
      setProblem(flow.report(e))
    }
    setBusy(null)
  }

  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState<string[]>([])
  const [editError, setEditError] = useState(false)
  const startEdit = (ref: string, times: string[]) => (setEditing(ref), setDraft(times), setEditError(false))
  const saveTimes = async () => {
    if (!data || !editing) return
    if (!validTimes(draft)) return setEditError(true)
    const overrides: Record<string, string[]> = Object.fromEntries(data.medicines.filter((m) => m.source === 'user').map((m) => [m.ref, m.times]))
    overrides[editing] = [...draft].sort()
    try {
      setData(await saveOverrides(id, { overrides }))
      setEditing(null)
    } catch (e) {
      setProblem(flow.report(e))
    }
  }

  if (!data) {
    return (
      <>
        <SectionHeading as="h1" label={t('ui.flow.stage.schedule')} title={t('ui.flow.schedule.title')} />
        {problem ? <ProblemNotice problem={problem} /> : <p role="status" className="muted">{t('ui.flow.loading')}</p>}
      </>
    )
  }

  const week = Array.from({ length: 7 }, (_, i) => localDate(addDays(new Date(), i - 3)))
  const daySlots = slots
  const isFuture = day > today
  const next = day === today ? nextDose(daySlots, now, (s) => !!evFor(s.med_ref, s.time, today)) : null
  const fmt = (d: string) => new Date(d + 'T12:00:00').toLocaleDateString(lang === 'en' ? 'en-IN' : lang === 'ta' ? 'ta-IN' : 'hi-IN', { weekday: 'short', day: 'numeric', month: 'short' })

  return (
    <>
      <SectionHeading as="h1" label={t('ui.flow.stage.schedule')} title={t('ui.flow.schedule.title')} />
      <DemoMarksNote />
      <Notice tone="important" title={t('ui.flow.schedule.no_reminders.title')}>
        <p>{t('ui.flow.schedule.no_reminders')}</p>
        <p>{data.notice.text}</p>
        {data.extra_notices.map((n) => <p key={n.template_id}>{n.text}</p>)}
      </Notice>
      {problem ? <ProblemNotice problem={problem} /> : null}

      <div className="week" role="group" aria-label={t('ui.flow.schedule.week')}>
        {week.map((d) => {
          const n = events.filter((e) => e.date === d).length
          return (
            <button key={d} type="button" aria-pressed={d === day} className={d === today ? 'today' : ''} onClick={() => setDay(d)}>
              <span>{fmt(d)}</span>
              <span className="small">{d === today ? t('ui.flow.schedule.today') : ''}</span>
              <span className="small"><Icon name="check" size={14} /> {n}/{slots.length}</span>
            </button>
          )
        })}
      </div>

      <section aria-labelledby="slots-h" className="res-section">
        <h2 id="slots-h" className="h3-like">{day === today ? t('ui.flow.schedule.today_slots') : fmt(day)}</h2>
        {next ? <p className="next-dose" role="status"><Icon name="clock" size={20} /><span>{t('ui.flow.schedule.next', { name: next.name, time: next.time })}</span></p> : null}
        {daySlots.length === 0 ? <p className="muted">{t('ui.flow.schedule.none')}</p> : null}
        {isFuture && daySlots.length ? <p className="small muted">{t('ui.flow.schedule.future')}</p> : null}
        <ul className="slot-list">
          {daySlots.map((sl) => {
            const e = evFor(sl.med_ref, sl.time)
            const key = `${sl.med_ref}|${sl.time}`
            return (
              <li key={key} className="slot">
                <span className="slot-time">{sl.time}</span>
                <span className="slot-name">{sl.name}</span>
                {sl.source === 'user' ? <span className="tag tag-neutral">{t('ui.flow.schedule.yours')}</span> : null}
                <span className="slot-actions" role="group" aria-label={`${sl.name} ${sl.time}`}>
                  <Button variant="secondary" aria-pressed={e?.status === 'taken'} disabled={isFuture || busy === key} icon={e?.status === 'taken' ? 'check' : undefined} onClick={() => mark(sl, 'taken')}>{t('ui.flow.schedule.taken')}</Button>
                  <Button variant="secondary" aria-pressed={e?.status === 'skipped'} disabled={isFuture || busy === key} icon={e?.status === 'skipped' ? 'close' : undefined} onClick={() => mark(sl, 'skipped')}>{t('ui.flow.schedule.skipped')}</Button>
                  {e ? <Button variant="quiet" disabled={busy === key} onClick={() => mark(sl, e.status)}>{t('ui.flow.schedule.undo')}</Button> : null}
                </span>
              </li>
            )
          })}
        </ul>
      </section>

      <section aria-labelledby="times-h" className="res-section">
        <h2 id="times-h" className="h3-like">{t('ui.flow.schedule.times_title')}</h2>
        <ul className="res-lines">
          {data.medicines.map((m) => (
            <li key={m.ref} className="res-line">
              <p><strong>{m.name}</strong> {[m.strength, m.dose, m.duration_text].filter(Boolean).join(' · ')}</p>
              {editing === m.ref ? <TimeEditor draft={draft} setDraft={setDraft} error={editError} onSave={saveTimes} onCancel={() => setEditing(null)} /> : (
                <p>{m.times.join(', ')} <Button variant="quiet" onClick={() => startEdit(m.ref, m.times)}>{t('ui.flow.schedule.edit_times')}</Button></p>
              )}
            </li>
          ))}
        </ul>
      </section>

      {data.not_scheduled.length ? (
        <section aria-labelledby="ns-h" className="res-section">
          <h2 id="ns-h" className="h3-like">{t('ui.flow.schedule.not_scheduled')}</h2>
          <ul className="res-lines">
            {data.not_scheduled.map((n) => (
              <li key={n.ref} className="res-line aggregate">
                <Icon name="circle-alert" size={18} />
                <div>
                  <p><strong>{n.name || n.ref}</strong></p>
                  <p>{n.text}</p>
                  {n.user_can_set_times ? (
                    editing === n.ref ? <TimeEditor draft={draft} setDraft={setDraft} error={editError} onSave={saveTimes} onCancel={() => setEditing(null)} /> : <Button variant="secondary" onClick={() => startEdit(n.ref, ['08:00'])}>{t('ui.flow.schedule.set_times')}</Button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="page-actions">
        <ButtonLink to={docPath(id, 'summary')} icon="document">{t('ui.flow.result.to_summary')}</ButtonLink>
        <ButtonLink to={docPath(id, 'result')} variant="quiet">{t('ui.flow.schedule.back_results')}</ButtonLink>
      </div>
    </>
  )
}

function TimeEditor({ draft, setDraft, error, onSave, onCancel }: { draft: string[]; setDraft: (v: string[]) => void; error: boolean; onSave: () => void; onCancel: () => void }) {
  const { t } = useT()
  return (
    <div className="time-editor">
      {draft.map((x, i) => (
        <div key={i} className="time-row">
          <label htmlFor={`te-${i}`} className="sr-only">{t('ui.flow.schedule.time_n', { n: i + 1 })}</label>
          <input id={`te-${i}`} type="time" value={x} onChange={(e) => setDraft(draft.map((y, k) => (k === i ? e.target.value : y)))} aria-invalid={error || undefined} />
          <Button variant="quiet" onClick={() => setDraft(draft.filter((_, k) => k !== i))} disabled={draft.length <= 1} aria-label={t('ui.flow.schedule.remove_time', { n: i + 1 })}>{t('ui.flow.schedule.remove')}</Button>
        </div>
      ))}
      {error ? <p role="alert" className="field-error"><Icon name="alert" size={18} /><span>{t('ui.flow.schedule.time_error')}</span></p> : null}
      <div className="page-actions">
        {draft.length < 6 ? <Button variant="secondary" icon="plus" onClick={() => setDraft([...draft, '12:00'])}>{t('ui.flow.schedule.add_time')}</Button> : null}
        <Button onClick={onSave}>{t('ui.flow.schedule.save_times')}</Button>
        <Button variant="quiet" onClick={onCancel}>{t('ui.flow.add.cancel')}</Button>
      </div>
    </div>
  )
}

