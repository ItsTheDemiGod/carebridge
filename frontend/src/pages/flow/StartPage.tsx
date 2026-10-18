import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Problem } from '../../api/errors'
import { Button, ButtonLink } from '../../components/Button'
import { Notice } from '../../components/Badges'
import { Icon, type IconName } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { TrySampleLink } from '../../demo/DemoBar'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { consentGranted } from '../../flow/state'
import { useT } from '../../i18n/I18n'

const STEPS: { n: string; icon: IconName }[] = [
  { n: '1', icon: 'camera' },
  { n: '2', icon: 'check' },
  { n: '3', icon: 'document' },
]

export function StartPage() {
  const { t } = useT()
  const flow = useFlow()
  const nav = useNavigate()
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<Problem | null>(null)
  const have = flow.state.session && consentGranted(flow.state)

  const begin = async () => {
    setBusy(true)
    const p = await flow.startSession()
    setBusy(false)
    if (p) setProblem(p)
    else nav('/consent')
  }

  return (
    <FlowPage titleKey="ui.title.start" need="none">
      <SectionHeading as="h1" label={t('ui.nav.start')} title={t('ui.start.title')} />
      <p className="lede">{t('ui.start.body')}</p>
      <ol className="steps-list">
        {STEPS.map((s) => (
          <li key={s.n}>
            <Icon name={s.icon} size={26} />
            <div>
              <p className="step-title">{t(`ui.flow.start.step${s.n}.title`)}</p>
              <p className="muted">{t(`ui.flow.start.step${s.n}.body`)}</p>
            </div>
          </li>
        ))}
      </ol>
      <Notice tone="info">
        <p>{t('ui.flow.start.local')}</p>
      </Notice>
      {problem ? <ProblemNotice problem={problem} /> : null}
      <div className="page-actions">
        {have ? (
          <>
            <ButtonLink to="/upload" icon="arrow">
              {t('ui.flow.start.continue')}
            </ButtonLink>
            <ButtonLink to="/documents" variant="secondary">
              {t('ui.flow.nav.documents')}
            </ButtonLink>
          </>
        ) : (
          <Button icon="arrow" loading={busy} onClick={begin}>
            {t('ui.flow.start.begin')}
          </Button>
        )}
        <ButtonLink to="/" variant="quiet">
          {t('ui.start.back')}
        </ButtonLink>
      </div>
      <TrySampleLink />
    </FlowPage>
  )
}
