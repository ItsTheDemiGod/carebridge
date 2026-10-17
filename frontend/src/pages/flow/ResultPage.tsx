import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getResult, startLanguage } from '../../api/endpoints'
import { isAbort, toProblem, type Problem } from '../../api/errors'
import { startPolling } from '../../api/poll'
import type { Lang, Level, PairResult, ResultLine, ResultResponse, ResultSection } from '../../api/types'
import { Button, ButtonLink } from '../../components/Button'
import { Notice, StatusBadge } from '../../components/Badges'
import { Icon, type IconName } from '../../components/icons'
import { IconHeading, SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { useServerStrings } from '../../flow/serverStrings'
import { useT } from '../../i18n/I18n'
import { LANGS } from '../../i18n/translate'

const SEC_ICON: Record<'follow_ups' | 'advice' | 'warnings', IconName> = { follow_ups: 'calendar', advice: 'leaf', warnings: 'alert' }

export function ResultPage() {
  const { id = '' } = useParams()
  return (
    <FlowPage titleKey="ui.title.result" narrow={false} className="result-page">
      <Result id={id} />
    </FlowPage>
  )
}

const RANK: Record<Level, number> = { major: 0, moderate: 1, minor: 2, unknown: 3 }
const FREE = new Set(['follow_ups', 'advice', 'warnings'])
const textOf = (l: ResultLine, lang: Lang) => l.text[lang]?.text ?? l.source_text

function Result({ id }: { id: string }) {
  const { t, lang: uiLang } = useT()
  const { s } = useServerStrings()
  const flow = useFlow()
  const sessionLang = flow.state.sessionLang
  const [rl, setRl] = useState<Lang>(uiLang)
  const [data, setData] = useState<ResultResponse | null>(null)
  const [problem, setProblem] = useState<Problem | null>(null)
  const [announce, setAnnounce] = useState('')
  const startedFor = useRef(new Set<string>())
  const prevPending = useRef<boolean | null>(null)

  useEffect(() => setRl(uiLang), [uiLang])

  useEffect(() => {
    if (!sessionLang) return
    setProblem(null)
    return startPolling<ResultResponse>({
      fetch: async (signal) => {
        const r = await getResult(id, rl, signal)
        if (r.narrative_status[rl] === 'not_started' && !startedFor.current.has(rl)) {
          startedFor.current.add(rl)
          await startLanguage(id, rl, signal) // the narrative for this language starts now; we keep polling until it is ready
        }
        return r
      },
      isDone: (r) => ['ready', 'failed'].includes(r.narrative_status[rl]),
      onValue: (r) => {
        setData(r)
        const pending = !['ready', 'failed'].includes(r.narrative_status[rl])
        if (prevPending.current && !pending) setAnnounce(t(r.narrative_status[rl] === 'ready' ? 'ui.flow.result.ready' : 'ui.flow.result.failed_note'))
        prevPending.current = pending
      },
      onError: (e) => {
        if (isAbort(e)) return false
        const p = toProblem(e)
        if (p.kind === 'network' || p.kind === 'server') return true
        setProblem(flow.report(e))
        return false
      },
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, rl, sessionLang])

  if (problem && !data) {
    return (
      <>
        <SectionHeading as="h1" label={t('ui.flow.stage.results')} title={t('ui.flow.result.title')} />
        <ProblemNotice problem={problem} />
        <div className="page-actions"><ButtonLink to={`/d/${id}/review`} variant="secondary">{t('ui.flow.result.back_review')}</ButtonLink></div>
      </>
    )
  }
  if (!data) {
    return (
      <>
        <SectionHeading as="h1" label={t('ui.flow.stage.results')} title={t('ui.flow.result.title')} />
        <p role="status" className="muted">{t('ui.flow.loading')}</p>
      </>
    )
  }

  const sections = data.explanation.sections
  const get = (sid: ResultSection['id']) => sections.find((x) => x.id === sid)
  const safety = get('safety')
  const banner = safety?.lines.find((l) => l.line_id === 'safety-banner')
  const found: PairResult[] = (data.explanation.safety?.pair_results ?? []).filter((p) => p.status === 'interaction_found').sort((a, b) => RANK[a.level ?? 'unknown'] - RANK[b.level ?? 'unknown'])
  const pairLines = safety?.lines.filter((l) => l.line_id.startsWith('safety-pair-')) ?? []
  const otherSafety = safety?.lines.filter((l) => l.line_id !== 'safety-banner' && !l.line_id.startsWith('safety-pair-')) ?? []
  const status = data.narrative_status[rl]
  const meta = Object.fromEntries(data.medicines_meta.map((m) => [m.line_id, m]))

  return (
    <>
      <SectionHeading as="h1" label={t('ui.flow.stage.results')} title={t('ui.flow.result.title')} />
      <p className="lede">{t('ui.flow.result.intro')}</p>

      <div className="result-tools no-print">
        <div role="tablist" aria-label={t('ui.flow.result.tabs')} className="tabs">
          {LANGS.map((l) => (
            <button key={l.code} role="tab" type="button" lang={l.code} id={`tab-${l.code}`} aria-selected={rl === l.code} aria-controls="result-panel" tabIndex={rl === l.code ? 0 : -1}
              onClick={() => setRl(l.code)}
              onKeyDown={(e) => {
                const i = LANGS.findIndex((x) => x.code === rl)
                const n = e.key === 'ArrowRight' ? (i + 1) % 3 : e.key === 'ArrowLeft' ? (i + 2) % 3 : -1
                if (n >= 0) {
                  e.preventDefault()
                  setRl(LANGS[n].code)
                  document.getElementById(`tab-${LANGS[n].code}`)?.focus()
                }
              }}>
              {l.name}
            </button>
          ))}
        </div>
        <Button variant="secondary" icon="document" onClick={() => window.print()}>{t('ui.flow.result.print')}</Button>
      </div>
      <p className="sr-only" role="status" aria-live="polite">{announce}</p>

      <div id="result-panel" role="tabpanel" aria-labelledby={`tab-${rl}`} lang={rl} className="result-panel">
        {rl !== 'en' ? <p className="draft-inline"><Icon name="info" size={18} /><span>{t('ui.draft_note')}</span></p> : null}
        {status === 'running' || status === 'pending' || status === 'not_started' ? (
          <p className="preparing" role="status"><span className="btn-spinner" aria-hidden="true" /><span>{t('ui.flow.result.preparing')}</span></p>
        ) : null}
        {status === 'failed' ? <Notice tone="caution"><p>{t('ui.flow.result.failed_note')}</p></Notice> : null}
        {problem ? <ProblemNotice problem={problem} /> : null}

        {banner ? (
          <Notice tone={data.confirm_first ? 'important' : 'caution'} title={t(data.confirm_first ? 'ui.flow.result.banner.confirm_first' : 'ui.flow.result.banner.review')}>
            <p>{textOf(banner, rl)}</p>
            {data.confirm_first ? <p><Link className="text-link" to={`/d/${id}/review`}>{t('ui.flow.result.back_review')}</Link></p> : null}
          </Notice>
        ) : null}

        {get('medicines') ? (
          <section aria-labelledby="sec-medicines" className="res-section">
            <IconHeading id="sec-medicines" icon="pill">{get('medicines')!.heading[rl]}</IconHeading>
            <ul className="res-lines">
              {get('medicines')!.lines.map((l) => (
                <li key={l.line_id} className={`res-line${l.review_level === 'must_confirm' ? ' must' : ''}`}>
                  <p className="line-text"><Icon name="pill" size={18} /><span>{textOf(l, rl)}</span></p>
                  <div className="chips">
                    {meta[l.line_id]?.labels.map((x) => <span key={x.template_id} className="tag tag-accent"><Icon name="check" size={14} /><span>{x.text}</span></span>)}
                    {chip(l, rl, t, s)}
                  </div>
                  {l.notices.map((n) => <p key={n.code} className="inline-note"><Icon name="alert" size={18} /><span>{n.text[rl]?.text}</span></p>)}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {(['follow_ups', 'advice', 'warnings'] as const).map((sid) => {
          const sec = get(sid)
          if (!sec || !FREE.has(sid) || !sec.lines.length) return null
          return (
            <section key={sid} aria-labelledby={`sec-${sid}`} className="res-section">
              <IconHeading id={`sec-${sid}`} icon={SEC_ICON[sid]}>{sec.heading[rl]}</IconHeading>
              <ul className="res-lines">
                {sec.lines.map((l) => (
                  <li key={l.line_id} className={`res-line${sid === 'warnings' ? ' warn' : ''}`}>
                    {l.narrative_pending ? <p className="preparing"><span className="btn-spinner" aria-hidden="true" /><span>{textOf(l, rl)}</span></p> : <p className="line-text">{sid === 'warnings' ? <Icon name="alert" size={18} /> : null}<span>{textOf(l, rl)}</span></p>}
                    <div className="chips">{l.narrative_pending ? null : chip(l, rl, t, s)}</div>
                    {l.notices.map((n) => <p key={n.code} className="inline-note"><Icon name="info" size={18} /><span>{n.text[rl]?.text}</span></p>)}
                  </li>
                ))}
              </ul>
            </section>
          )
        })}

        {safety ? (
          <section aria-labelledby="sec-safety" className="res-section">
            <IconHeading id="sec-safety" icon="shield">{safety.heading[rl]}</IconHeading>
            <ul className="res-lines pairs">
              {found.map((p, k) => {
                const line = pairLines[k]
                const lvl = p.level ?? 'unknown'
                return (
                  <li key={`${p.a}-${p.b}`} className={`pair-card sev-${lvl}`}>
                    <div className="pair-head">
                      <StatusBadge level={lvl}>{t(`ui.flow.level.${lvl}`)}</StatusBadge>
                      <span className="pair-names">{[p.generic_a, p.generic_b].filter(Boolean).join(' + ')}</span>
                    </div>
                    {line ? <p>{textOf(line, rl)}</p> : null}
                    <p className="small muted">{t('ui.flow.result.source')}: {sourceLabel(p.source, t)}</p>
                  </li>
                )
              })}
            </ul>
            <ul className="res-lines plain">
              {otherSafety.map((l) => (
                <li key={l.line_id} className="res-line aggregate"><Icon name="info" size={18} /><p>{textOf(l, rl)}</p></li>
              ))}
            </ul>
          </section>
        ) : null}

        {get('not_found')?.lines.length ? (
          <section aria-labelledby="sec-nf" className="res-section">
            <IconHeading id="sec-nf" icon="search">{get('not_found')!.heading[rl]}</IconHeading>
            <ul className="res-lines">{get('not_found')!.lines.map((l) => <li key={l.line_id} className="res-line"><p>{textOf(l, rl)}</p></li>)}</ul>
          </section>
        ) : null}

        {get('disclaimer')?.lines.length ? <Notice tone="info" title={get('disclaimer')!.heading[rl]}>{get('disclaimer')!.lines.map((l) => <p key={l.line_id}>{textOf(l, rl)}</p>)}</Notice> : null}
        <p className="small muted">{t('ui.flow.result.not_advice')}</p>
      </div>

      <div className="page-actions no-print">
        <ButtonLink to={`/d/${id}/schedule`} icon="clock">{t('ui.flow.result.to_schedule')}</ButtonLink>
        <ButtonLink to={`/d/${id}/summary`} variant="secondary" icon="document">{t('ui.flow.result.to_summary')}</ButtonLink>
        <ButtonLink to={`/d/${id}/review`} variant="quiet">{t('ui.flow.result.back_review')}</ButtonLink>
      </div>
    </>
  )
}

function sourceLabel(src: PairResult['source'], t: (k: string) => string): string {
  return src === 'ddinter' ? t('ui.flow.source.ddinter') : src === 'curated_author_checked' ? t('ui.flow.source.author') : src === 'curated_reviewed' ? t('ui.flow.source.curated') : t('ui.flow.source.unknown')
}

/** The trust chip for one line: what kind of text it is, never a claim of human review. */
function chip(l: ResultLine, lang: Lang, t: (k: string) => string, s: (id: string) => string) {
  const k = l.text[lang]?.label_key
  const label = k === 'draft_unreviewed' ? s('label.draft_unreviewed') : k === 'machine_checked' ? s('label.machine_checked') : k === 'original_only' ? t('ui.flow.label.original') : ''
  return label ? <span className={`tag ${k === 'original_only' ? 'tag-neutral' : 'tag-draft'}`}><Icon name={k === 'original_only' ? 'document' : 'language'} size={14} /><span>{label}</span></span> : null
}
