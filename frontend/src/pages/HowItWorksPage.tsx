import { Notice, Tag } from '../components/Badges'
import { Icon, type IconName } from '../components/icons'
import { Container, SectionHeading } from '../components/Layout'
import { PipelineDiagram } from '../components/PipelineDiagram'
import { useT } from '../i18n/I18n'
import { usePageTitle } from './usePageTitle'

const STEPS = ['n1', 'n2', 'n3', 'n4', 'n5'] as const
const YOURS = new Set(['n1', 'n3'])
const STEP_ICON: Record<(typeof STEPS)[number], IconName> = { n1: 'camera', n2: 'document', n3: 'check', n4: 'language', n5: 'search' }

export function HowItWorksPage() {
  const { t } = useT()
  usePageTitle('ui.title.how')
  return (
    <Container as="section" className="page-wide">
      <SectionHeading as="h1" label={t('ui.nav.how')} title={t('ui.how.title')} />
      <p className="lede">{t('ui.how.intro')}</p>
      <div className="pipeline-wrap">
        <PipelineDiagram />
      </div>
      <ol className="how-list">
        {STEPS.map((n, i) => (
          <li key={n}>
            <span className="how-num" aria-hidden="true">{`0${i + 1}`}</span>
            <div>
              <h3 className="icon-heading">
                <Icon name={STEP_ICON[n]} size={22} />
                <span>{t(`ui.how.${n}.title`)}</span>
              </h3>
              <p>{t(`ui.how.${n}.body`)}</p>
              {YOURS.has(n) ? <Tag tone="accent" icon="check">{t('ui.how.you')}</Tag> : null}
            </div>
          </li>
        ))}
      </ol>
      <Notice tone="important">
        <p>{t('ui.how.unchecked_note')}</p>
      </Notice>
    </Container>
  )
}
