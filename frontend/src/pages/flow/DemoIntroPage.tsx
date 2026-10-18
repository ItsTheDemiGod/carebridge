import { useEffect } from 'react'
import { Icon, type IconName } from '../../components/icons'
import { ButtonLink } from '../../components/Button'
import { Container, SectionHeading } from '../../components/Layout'
import { preloadDemo } from '../../demo/demoApi'
import { DemoBar } from '../../demo/DemoBar'
import { useT } from '../../i18n/I18n'
import { usePageTitle } from '../usePageTitle'

const STEPS: { n: string; icon: IconName }[] = [
  { n: 's1', icon: 'check' },
  { n: 's2', icon: 'language' },
  { n: 's3', icon: 'clock' },
]

/** /demo: says plainly what the sample is. Also loads the recordings and the sample photo once, so the rest of the sample needs no network. */
export function DemoIntroPage() {
  const { t } = useT()
  usePageTitle('ui.title.demo')
  useEffect(() => {
    preloadDemo().catch(() => {})
  }, [])
  return (
    <Container as="section" className="page-narrow flow-page">
      <DemoBar />
      <SectionHeading as="h1" label={t('ui.demo.intro.label')} title={t('ui.demo.intro.title')} />
      <p className="lede">{t('ui.demo.intro.body1')}</p>
      <p>{t('ui.demo.intro.body2')}</p>
      <ol className="steps-list">
        {STEPS.map((s) => (
          <li key={s.n}>
            <Icon name={s.icon} size={26} />
            <div>
              <p className="step-title">{t(`ui.demo.intro.${s.n}`)}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="muted">{t('ui.demo.intro.not_advice')}</p>
      <div className="page-actions">
        <ButtonLink to="/demo/review" icon="arrow">
          {t('ui.demo.intro.start')}
        </ButtonLink>
      </div>
    </Container>
  )
}
