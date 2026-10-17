import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { consentNotice } from '../../api/endpoints'
import { isAbort, toProblem, type Problem } from '../../api/errors'
import type { ConsentNotice } from '../../api/types'
import { Button } from '../../components/Button'
import { Notice } from '../../components/Badges'
import { Icon, type IconName } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { useT } from '../../i18n/I18n'

const OPTIONAL_HELP: Record<string, string> = { keep_photo_for_session: 'ui.flow.consent.keep_photo_help' }

/** one icon per notice item (the item text carries the meaning; the icon only helps scanning) */
const NOTICE_ICON: Record<string, IconName> = { what: 'document', where: 'lock', stored: 'clock', how_long: 'calendar', delete: 'trash', no_sharing: 'shield', prototype: 'info', translation_draft: 'language', interaction_limited: 'circle-alert', contact: 'info' }

export function ConsentPage() {
  const { t, lang } = useT()
  const flow = useFlow()
  const nav = useNavigate()
  const [notice, setNotice] = useState<ConsentNotice | null>(null)
  const [loadProblem, setLoadProblem] = useState<Problem | null>(null)
  const [optional, setOptional] = useState<Record<string, boolean>>({}) // nothing optional is pre-ticked
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<Problem | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const ctl = new AbortController()
    setNotice(null)
    setLoadProblem(null)
    consentNotice(lang, ctl.signal)
      .then(setNotice)
      .catch((e) => !isAbort(e) && setLoadProblem(toProblem(e)))
    return () => ctl.abort()
  }, [lang, attempt])

  const accept = async () => {
    if (!notice) return
    setBusy(true)
    setProblem(null)
    const purposes = notice.purposes.filter((p) => p.required || optional[p.id]).map((p) => p.id)
    const p = await flow.giveConsent(notice.version, purposes)
    setBusy(false)
    if (p) {
      setProblem(p)
      // a notice version change between load and accept: reload the notice so the person reads the current one
      if (p.code === 'consent_invalid') setAttempt((n) => n + 1)
    } else nav('/upload')
  }

  return (
    <FlowPage titleKey="ui.title.consent" need="session">
      <SectionHeading as="h1" label={t('ui.flow.stage.consent')} title={t('ui.flow.consent.title')} />
      <p className="lede">{t('ui.flow.consent.intro')}</p>
      <div aria-live="polite">
        {!notice && !loadProblem ? <p className="muted" role="status">{t('ui.pp.loading')}</p> : null}
        {loadProblem ? (
          <Notice tone="caution">
            <p>{t('ui.error.backend')}</p>
            <div className="page-actions">
              <Button variant="secondary" onClick={() => setAttempt((n) => n + 1)}>{t('ui.flow.retry')}</Button>
            </div>
          </Notice>
        ) : null}
      </div>
      {notice ? (
        <form
          className="consent-article"
          onSubmit={(e) => {
            e.preventDefault()
            void accept()
          }}
        >
          <p className="label">{t('ui.pp.version', { version: notice.version })}</p>
          <h2 className="h3-like">{notice.title}</h2>
          <ol className="consent-list">
            {notice.items.map((i) => (
              <li key={i.id}>
                <div className="consent-item">
                  <Icon name={NOTICE_ICON[i.id] ?? 'info'} size={22} />
                  <span>{i.text}</span>
                </div>
              </li>
            ))}
          </ol>
          <fieldset className="purposes">
            <legend className="label">{t('ui.flow.consent.purposes')}</legend>
            {notice.purposes.map((p) => (
              <div key={p.id} className="check-row">
                <input
                  id={`purpose-${p.id}`}
                  type="checkbox"
                  checked={p.required ? true : !!optional[p.id]}
                  disabled={!!p.required}
                  aria-describedby={OPTIONAL_HELP[p.id] ? `help-${p.id}` : undefined}
                  onChange={(e) => setOptional((o) => ({ ...o, [p.id]: e.target.checked }))}
                />
                <label htmlFor={`purpose-${p.id}`}>
                  {p.label}
                  {p.required ? <span className="tag tag-neutral req-tag">{t('ui.flow.consent.required')}</span> : <span className="tag tag-accent req-tag">{t('ui.flow.consent.optional')}</span>}
                </label>
                {OPTIONAL_HELP[p.id] ? (
                  <p id={`help-${p.id}`} className="small muted check-help">
                    {t(OPTIONAL_HELP[p.id])}
                  </p>
                ) : null}
              </div>
            ))}
          </fieldset>
          {problem ? <ProblemNotice problem={problem} /> : null}
          <div className="page-actions">
            <Button type="submit" icon="arrow" loading={busy}>
              {t('ui.flow.consent.accept')}
            </Button>
          </div>
        </form>
      ) : null}
    </FlowPage>
  )
}
