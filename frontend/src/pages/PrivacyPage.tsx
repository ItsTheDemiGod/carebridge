import { useCallback, useEffect, useState } from 'react'
import { getConsentNotice, type ConsentNotice } from '../api/client'
import { Button, ButtonLink } from '../components/Button'
import { Notice } from '../components/Badges'
import { Container, SectionHeading } from '../components/Layout'
import { SampleLink } from '../demo/DemoBar'
import { useT } from '../i18n/I18n'
import { DEMO_ONLY } from '../lib/mode'
import { usePageTitle } from './usePageTitle'

type State = { kind: 'loading' } | { kind: 'error' } | { kind: 'ok'; notice: ConsentNotice }

/** The only page that talks to the backend in Phase 6a: it shows the live consent notice. */
export function PrivacyPage() {
  const { t, lang } = useT()
  usePageTitle('ui.title.privacy')
  const [state, setState] = useState<State>({ kind: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const ctl = new AbortController()
    setState({ kind: 'loading' })
    if (DEMO_ONLY) {
      // hosted sample: the notice was copied into the build from the same templates (scripts/build_static_privacy.py); no request
      void import('../data/consent-notice.generated.json').then((m) => setState({ kind: 'ok', notice: (m.default as unknown as Record<string, ConsentNotice>)[lang] }))
      return
    }
    getConsentNotice(lang, ctl.signal)
      .then((notice) => setState({ kind: 'ok', notice }))
      .catch((e) => {
        if (!(e instanceof DOMException && e.name === 'AbortError')) setState({ kind: 'error' })
      })
    return () => ctl.abort()
  }, [lang, attempt])
  const retry = useCallback(() => setAttempt((n) => n + 1), [])

  return (
    <Container as="section" className="page-narrow">
      <SectionHeading as="h1" label={t('ui.nav.privacy')} title={t('ui.pp.title')} />
      <p className="lede">{DEMO_ONLY ? t('ui.hosted.pp.intro') : t('ui.pp.intro')}</p>

      <div className="notice-slot" aria-live="polite">
        {state.kind === 'loading' ? <p className="muted">{t('ui.pp.loading')}</p> : null}
        {state.kind === 'error' ? (
          <Notice tone="caution">
            <p>{t('ui.error.backend')}</p>
            <div className="page-actions">
              <Button variant="secondary" onClick={retry}>
                {t('ui.pp.retry')}
              </Button>
            </div>
            <SampleLink />
          </Notice>
        ) : null}
        {state.kind === 'ok' ? (
          <article className="consent-article">
            <p className="label">{t('ui.pp.version', { version: state.notice.version })}</p>
            {DEMO_ONLY ? <p className="muted small">{t('ui.hosted.pp.note', { version: state.notice.version })}</p> : null}
            <h2 className="h3-like">{state.notice.title}</h2>
            <ol className="consent-list">
              {state.notice.items.map((i) => (
                <li key={i.id}>{i.text}</li>
              ))}
            </ol>
            <ul className="consent-purposes">
              {state.notice.purposes.map((p) => (
                <li key={p.id}>{p.label}</li>
              ))}
            </ul>
          </article>
        ) : null}
      </div>

      <Notice tone="important" title={t('ui.pp.delete.title')}>
        <p>{DEMO_ONLY ? t('ui.hosted.pp.nodelete') : t('ui.pp.delete.body')}</p>
        {DEMO_ONLY ? null : (
          <ButtonLink to="/documents" variant="secondary" icon="trash">
            {t('ui.flow.delete.button')}
          </ButtonLink>
        )}
      </Notice>
    </Container>
  )
}
