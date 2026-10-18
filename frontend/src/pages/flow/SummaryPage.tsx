import { useEffect, useState } from 'react'
import { getDoctorSummary } from '../../api/endpoints'
import { isAbort, type Problem } from '../../api/errors'
import type { DoctorSummary } from '../../api/types'
import { Button, ButtonLink } from '../../components/Button'
import { Notice } from '../../components/Badges'
import { Icon } from '../../components/icons'
import { IconHeading, SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { useDocId, useDocPath } from '../../demo/useDemo'
import { useT } from '../../i18n/I18n'

export function SummaryPage() {
  const id = useDocId()
  return (
    <FlowPage titleKey="ui.title.summary" narrow={false} className="summary-page">
      <Summary id={id} />
    </FlowPage>
  )
}

function Summary({ id }: { id: string }) {
  const docPath = useDocPath()
  const { t } = useT()
  const flow = useFlow()
  const sessionLang = flow.state.sessionLang
  const [data, setData] = useState<DoctorSummary | null>(null)
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [range, setRange] = useState<{ from?: string; to?: string }>({})
  const [problem, setProblem] = useState<Problem | null>(null)

  useEffect(() => {
    if (!sessionLang) return
    const ctl = new AbortController()
    getDoctorSummary(id, range.from, range.to, ctl.signal)
      .then((d) => {
        setData(d)
        setFrom(d.period.from)
        setTo(d.period.to)
        setProblem(null)
      })
      .catch((e) => !isAbort(e) && setProblem(flow.report(e)))
    return () => ctl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, sessionLang, range])

  const head = <SectionHeading as="h1" label={t('ui.flow.stage.schedule')} title={data?.title ?? t('ui.flow.summary.title')} />
  if (!data) return <>{head}{problem ? <ProblemNotice problem={problem} /> : <p role="status" className="muted">{t('ui.flow.loading')}</p>}</>

  const bad = from !== '' && to !== '' && to < from
  return (
    <>
      {head}
      <form className="range no-print" onSubmit={(e) => { e.preventDefault(); if (!bad) setRange({ from, to }) }}>
        <div><label htmlFor="r-from" className="field-label">{t('ui.flow.summary.from')}</label><input id="r-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></div>
        <div><label htmlFor="r-to" className="field-label">{t('ui.flow.summary.to')}</label><input id="r-to" type="date" value={to} onChange={(e) => setTo(e.target.value)} aria-invalid={bad || undefined} /></div>
        <Button type="submit" variant="secondary" disabled={bad}>{t('ui.flow.summary.apply')}</Button>
        <Button type="button" icon="document" onClick={() => window.print()}>{t('ui.flow.result.print')}</Button>
      </form>
      {bad ? <p role="alert" className="field-error"><Icon name="alert" size={18} /><span>{t('ui.flow.summary.range_error')}</span></p> : null}
      {problem ? <ProblemNotice problem={problem} /> : null}
      <p className="muted">{t('ui.flow.summary.period', { from: data.period.from, to: data.period.to })}</p>

      <section aria-labelledby="s-meds" className="res-section">
        <IconHeading id="s-meds" icon="pill">{data.headings.medicines}</IconHeading>
        {data.medicines.length === 0 ? <p className="muted">{t('ui.flow.summary.no_meds')}</p> : (
          <div className="table-wrap" tabIndex={0} role="region" aria-label={data.headings.medicines}>
            <table className="summary-table">
              <thead>
                <tr>
                  <th scope="col">{t('ui.flow.summary.col.medicine')}</th>
                  <th scope="col">{t('ui.flow.summary.col.times')}</th>
                  <th scope="col">{data.labels.taken}</th>
                  <th scope="col">{data.labels.skipped}</th>
                  <th scope="col">{data.labels.missed}</th>
                </tr>
              </thead>
              <tbody>
                {data.medicines.map((m) => (
                  <tr key={m.ref}>
                    <th scope="row">{m.name}<br /><span className="small muted">{[m.strength, m.dose, m.duration_text].filter(Boolean).join(' · ')}</span></th>
                    <td>{m.times.join(', ')}</td>
                    <td>{m.taken}</td>
                    <td>{m.skipped}</td>
                    <td>{m.missed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="small muted">{data.schedule_notice}</p>
      </section>

      {data.not_scheduled.length ? (
        <section aria-labelledby="s-ns" className="res-section">
          <IconHeading id="s-ns" icon="calendar">{t('ui.flow.schedule.not_scheduled')}</IconHeading>
          <ul className="res-lines">{data.not_scheduled.map((n) => <li key={n.ref} className="res-line"><p><strong>{n.name}</strong>: {n.text}</p></li>)}</ul>
        </section>
      ) : null}

      <section aria-labelledby="s-unc" className="res-section">
        <IconHeading id="s-unc" icon="circle-alert">{data.headings.unconfirmed}</IconHeading>
        {data.unconfirmed.length === 0 ? <p className="muted">{t('ui.flow.summary.none')}</p> : (
          <ul className="res-lines">
            {data.unconfirmed.map((u) => (
              <li key={u.ref} className="res-line must"><p><strong>{u.name || u.ref}</strong></p>{u.reasons.map((r) => <p key={r.id} className="small">{r.text}</p>)}</li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="s-int" className="res-section">
        <IconHeading id="s-int" icon="shield">{data.headings.interactions}</IconHeading>
        {data.interactions.lines.length === 0 ? <p className="muted">{t('ui.flow.summary.none')}</p> : <ul className="res-lines">{data.interactions.lines.map((l, i) => <li key={i} className="res-line"><p>{l}</p></li>)}</ul>}
      </section>

      <Notice tone="info"><p>{data.disclaimer}</p></Notice>
      <div className="page-actions no-print">
        <ButtonLink to={docPath(id, 'schedule')} variant="secondary" icon="clock">{t('ui.flow.summary.back_schedule')}</ButtonLink>
        <ButtonLink to={docPath(id, 'result')} variant="quiet">{t('ui.flow.schedule.back_results')}</ButtonLink>
      </div>
    </>
  )
}
