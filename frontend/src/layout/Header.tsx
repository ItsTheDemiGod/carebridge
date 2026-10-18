import { useRef, useState, useSyncExternalStore } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useMotion } from '../ambient/motion'
import { Icon } from '../components/icons'
import { useIsDemo } from '../demo/useDemo'
import { DeleteControl } from '../flow/DeleteControl'
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

/** matchMedia as external state: correct on the first render, no flash of the wrong layout */
function useMedia(query: string) {
  return useSyncExternalStore(
    (cb) => {
      const m = window.matchMedia(query)
      m.addEventListener('change', cb)
      return () => m.removeEventListener('change', cb)
    },
    () => window.matchMedia(query).matches,
    () => false,
  )
}

function CalmToggle() {
  const { t } = useT()
  const { calm, setCalm } = useMotion()
  return (
    <button type="button" className="calm-toggle" aria-pressed={calm} aria-describedby="calm-explain" onClick={() => setCalm(!calm)}>
      <Icon name={calm ? 'still' : 'wave'} size={20} />
      <span className="calm-label">{t('ui.calm.label')}</span>
      <span className="calm-state">{calm ? t('ui.calm.on') : t('ui.calm.off')}</span>
    </button>
  )
}

/** One row from 64 rem up (brand, nav, Start, tools). Below that, a menu button opens a disclosure panel holding the same single set of controls. */
export function Header() {
  const { t, lang } = useT()
  const loc = useLocation()
  // one row from 64 rem (English, Hindi) or 80 rem (Tamil: its labels are about twice as wide); below that the menu button
  const row = useMedia(lang === 'ta' ? '(min-width: 80rem)' : '(min-width: 64rem)')
  const [openKey, setOpenKey] = useState<string | null>(null)
  const open = openKey === loc.key // the panel belongs to the page it was opened on, so any route change closes it
  const btn = useRef<HTMLButtonElement>(null)
  const demo = useIsDemo()
  return (
    <header
      className="site-header"
      data-layout={row ? 'row' : 'menu'}
      onKeyDown={(e) => {
        if (e.key === 'Escape' && open) {
          setOpenKey(null)
          btn.current?.focus()
        }
      }}
    >
      <div className="container header-row">
        <Link to="/" className="brand-link" aria-label={t('ui.brand.home')}>
          <Wordmark />
        </Link>
        {demo ? <span className="sample-tag">{t('ui.demo.tag')}</span> : null}
        <button ref={btn} type="button" className="menu-btn" aria-expanded={open} aria-controls="site-menu" onClick={() => setOpenKey(open ? null : loc.key)}>
          <Icon name={open ? 'close' : 'menu'} size={20} />
          <span>{t('ui.nav.menu')}</span>
        </button>
        <div id="site-menu" className="header-menu" data-open={open}>
          <nav className="site-nav" aria-label={t('ui.nav.label')}>
            <NavLink to="/how-it-works">{t('ui.nav.how_c')}</NavLink>
            <NavLink to="/privacy">{t('ui.nav.privacy')}</NavLink>
            <Link to="/#limits">{t('ui.nav.limits')}</Link>
            <NavLink to="/documents">{t('ui.nav.docs_c')}</NavLink>
          </nav>
          <NavLink to="/start" className="btn btn-primary nav-start">
            {t('ui.nav.start_c')}
          </NavLink>
          <div className="header-tools">
            <DeleteControl />
            <LanguageSwitcher />
            <CalmToggle />
          </div>
        </div>
      </div>
    </header>
  )
}
