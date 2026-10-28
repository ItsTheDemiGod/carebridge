import { ButtonLink } from '../components/Button'
import { Notice } from '../components/Badges'
import { Container, SectionHeading } from '../components/Layout'
import { useT } from '../i18n/I18n'
import { REPO_URL } from '../lib/mode'
import { usePageTitle } from './usePageTitle'

/** Hosted sample build only: shown for every route of the real flow. No request is made; nothing can be uploaded here. */
export function SampleOnlyPage() {
  const { t } = useT()
  usePageTitle('ui.title.hosted')
  return (
    <Container as="section" className="page-narrow">
      <SectionHeading as="h1" label={t('ui.demo.tag')} title={t('ui.hosted.title')} />
      <Notice tone="important">
        <p>{t('ui.hosted.body1')}</p>
      </Notice>
      <p className="lede">{t('ui.hosted.body2')}</p>
      <div className="page-actions">
        <ButtonLink to="/demo" icon="arrow">
          {t('ui.demo.try')}
        </ButtonLink>
        <a className="btn btn-secondary" href={REPO_URL} target="_blank" rel="noopener noreferrer">
          {t('ui.hosted.link_repo')}
        </a>
      </div>
    </Container>
  )
}
