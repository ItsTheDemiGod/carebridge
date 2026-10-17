import { useEffect, useRef, type ReactNode } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'
import { Notice } from '../components/Badges'
import { Container } from '../components/Layout'
import { useT } from '../i18n/I18n'
import { usePageTitle } from '../pages/usePageTitle'
import { useFlow } from './FlowProvider'
import { Progress } from './Progress'
import { consentGranted } from './state'

type Need = 'none' | 'session' | 'consent'

/** Common frame of every flow page: title, progress, session/consent gate (loading, expired, offline), focus on the page heading. */
export function FlowPage({ titleKey, need = 'consent', narrow = true, className = '', children }: { titleKey: string; need?: Need; narrow?: boolean; className?: string; children: ReactNode }) {
  const { t } = useT()
  const flow = useFlow()
  const nav = useNavigate()
  const { state } = flow
  usePageTitle(titleKey)

  let gate: ReactNode = null
  let open = true
  if (state.boot === 'idle' || state.boot === 'loading') {
    open = false
    gate = <p role="status" className="muted">{t('ui.flow.loading')}</p>
  } else if (state.boot === 'error') {
    open = false
    gate = (
      <Notice tone="caution" title={t('ui.flow.problem.network.title')}>
        <p>{t('ui.flow.problem.network')}</p>
        <div className="page-actions">
          <Button variant="secondary" onClick={flow.retryBoot}>{t('ui.flow.retry')}</Button>
        </div>
      </Notice>
    )
  } else if (state.boot === 'no_session' && need !== 'none') {
    open = false
    gate =
      state.problem?.kind === 'expired' ? (
        <Notice tone="important" title={t('ui.flow.expired.title')}>
          <p>{t('ui.flow.expired.body')}</p>
          <div className="page-actions">
            <Button
              onClick={() => {
                flow.clearProblem()
                nav('/start')
              }}
            >
              {t('ui.flow.expired.again')}
            </Button>
          </div>
        </Notice>
      ) : (
        <Navigate to={state.deleted ? '/' : '/start'} replace />
      )
  } else if (need === 'consent' && state.boot === 'ready' && !consentGranted(state)) {
    open = false
    gate = <Navigate to="/consent" replace />
  }

  const root = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const h = root.current?.querySelector('h1')
    if (h) {
      h.setAttribute('tabindex', '-1')
      h.focus({ preventScroll: true })
    }
  }, [open])

  return (
    <Container as="section" className={`${narrow ? 'page-narrow' : 'page-wide'} flow-page ${className}`.trim()}>
      <Progress />
      <div ref={root} className="flow-body">
        {open ? children : gate}
      </div>
    </Container>
  )
}
