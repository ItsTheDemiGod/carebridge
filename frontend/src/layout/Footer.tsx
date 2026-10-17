import { Link } from 'react-router-dom'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import manifest from '../photos.manifest.json'
import { Wordmark } from './Wordmark'

const CREDITS = Object.values(manifest as Record<string, { credit?: string }>).flatMap((e) => (e.credit ? [e.credit] : []))

export function Footer() {
  const { t } = useT()
  return (
    <footer className="site-footer on-dark">
      <div className="container footer-grid">
        <div>
          <Wordmark />
          <p className="footer-statement">{t('ui.footer.prototype')}</p>
        </div>
        <div className="footer-col">
          <p className="footer-contact">
            <Icon name="info" size={20} />
            <Link to="/privacy">{t('ui.footer.contact')}</Link>
          </p>
          <p className="footer-contact">
            <Icon name="trash" size={20} />
            <Link to="/documents">{t('ui.flow.delete.button')}</Link>
          </p>
          <p id="calm-explain" className="footer-small">
            <strong>{t('ui.calm.label')}.</strong> {t('ui.calm.explain')}
          </p>
          <p className="footer-small">
            <strong>{t('ui.footer.credits')}.</strong> {t('ui.footer.credits_body')}
          </p>
          {CREDITS.length ? <p className="footer-small footer-credits">{CREDITS.join(' · ')}</p> : null}
        </div>
      </div>
    </footer>
  )
}
