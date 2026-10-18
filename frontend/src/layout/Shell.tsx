import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef } from 'react'
import { useLocation, useOutlet } from 'react-router-dom'
import { CursorRing } from '../ambient/CursorRing'
import { FrameMonitor } from '../ambient/FrameMonitor'
import { useMotion } from '../ambient/motion'
import { ParticleField } from '../ambient/ParticleField'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { useIsDemo } from '../demo/useDemo'
import { FlowProvider } from '../flow/FlowProvider'
import { Footer } from './Footer'
import { Header } from './Header'

function DraftNote() {
  const { t, lang } = useT()
  if (lang === 'en') return null
  return (
    <div className="draft-note" role="note">
      <div className="container draft-note-row">
        <Icon name="info" size={18} />
        <span>{t('ui.draft_note')}</span>
      </div>
    </div>
  )
}

export function Shell() {
  const demo = useIsDemo()
  return (
    // a separate provider for the sample, so nothing of a real session (or the other way round) is ever shown in it
    <FlowProvider key={demo ? 'demo' : 'real'}>
      <ShellInner />
    </FlowProvider>
  )
}

function ShellInner() {
  const { t } = useT()
  const { motionOk } = useMotion()
  const loc = useLocation()
  const outlet = useOutlet() // captured per render: an exiting page keeps its own element instead of re-rendering the new route (no double mount)
  const main = useRef<HTMLElement>(null)
  const first = useRef(true)
  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    if (loc.hash) {
      requestAnimationFrame(() => document.getElementById(loc.hash.slice(1))?.scrollIntoView())
    } else {
      window.scrollTo(0, 0)
      if (!main.current?.contains(document.activeElement)) main.current?.focus({ preventScroll: true }) // move keyboard and screen-reader position to the new page (flow pages focus their own heading)
    }
  }, [loc.pathname, loc.hash])

  return (
    <>
      <a className="skip-link" href="#main">
        {t('ui.skip')}
      </a>
      <ParticleField />
      <CursorRing />
      <Header />
      <DraftNote />
      <main id="main" ref={main} tabIndex={-1}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div key={loc.pathname} initial={motionOk ? { opacity: 0, y: 10 } : false} animate={{ opacity: 1, y: 0 }} exit={motionOk ? { opacity: 0 } : { opacity: 1 }} transition={{ duration: motionOk ? 0.22 : 0 }}>
            {outlet}
          </motion.div>
        </AnimatePresence>
      </main>
      <Footer />
      <FrameMonitor />
    </>
  )
}
