import { Container } from '../components/Layout'
import { useT } from '../i18n/I18n'
import { usePageTitle } from './usePageTitle'

export function LandingPage() {
  const { t } = useT()
  usePageTitle('ui.title.home')
  return (
    <Container as="section">
      <h1 className="display">{t('ui.hero.title')}</h1>
    </Container>
  )
}
