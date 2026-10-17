import { ButtonLink } from '../components/Button'
import { Container, SectionHeading } from '../components/Layout'
import { useT } from '../i18n/I18n'
import { usePageTitle } from './usePageTitle'

export function NotFoundPage() {
  const { t } = useT()
  usePageTitle('ui.title.notfound')
  return (
    <Container as="section" className="page-narrow">
      <SectionHeading as="h1" label="404" title={t('ui.notfound.title')} />
      <p className="lede">{t('ui.notfound.body')}</p>
      <div className="page-actions">
        <ButtonLink to="/" icon="arrow">
          {t('ui.notfound.link')}
        </ButtonLink>
      </div>
    </Container>
  )
}
