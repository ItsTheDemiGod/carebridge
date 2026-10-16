import { Link, NavLink } from 'react-router-dom'
import { useMotion } from '../ambient/motion'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { LANGS } from '../i18n/translate'
import { Wordmark } from './Wordmark'

function LanguageSwitcher() {
  const { t, lang, setLang } = useT()
  return (
    <div className="lang-switch" role="group" aria-label={t('ui.lang.group')}>
      <Icon name="language" size={20} aria-hidden />
      {LANGS.map((l) => (
        <button key={l.code} type="button" lang={l.code} aria-pressed={lang === l.code} onClick={() => setLang(l.code)}>
          {l.name}
        </button>
      ))}
    </div>
  )
}

function CalmToggle() {
  const { t } = useT()
  const { calm, setCalm } = useMotion()
  return (
    <button type="button" className="calm-toggle" aria-pressed={calm} aria-describedby="calm-explain" onClick={() => setCalm(!calm)}>
      <Icon name="wave" size={20} />
      <span>{t('ui.calm.label')}</span>
      <span className="calm-state">{calm ? t('ui.calm.on') : t('ui.calm.off')}</span>
    </button>
  )
}

export function Header() {
  const { t } = useT()
  return (
    <header className="site-header">
      <div className="container header-row">
        <Link to="/" className="brand-link" aria-label={t('ui.brand.home')}>
          <Wordmark />
        </Link>
        <nav className="site-nav" aria-label={t('ui.nav.label')}>
          <NavLink to="/how-it-works">{t('ui.nav.how')}</NavLink>
          <NavLink to="/privacy">{t('ui.nav.privacy')}</NavLink>
          <Link to="/#limits">{t('ui.nav.limits')}</Link>
          <NavLink to="/start" className="nav-start">
            {t('ui.nav.start')}
          </NavLink>
        </nav>
        <div className="header-tools">
          <LanguageSwitcher />
          <CalmToggle />
        </div>
      </div>
    </header>
  )
}
