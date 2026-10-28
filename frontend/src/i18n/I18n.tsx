import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Lang } from '../api/client'
import { isDemoPath } from '../demo/demoApi'
import { DEMO_ONLY } from '../lib/mode'
import { readPref, writePref } from '../lib/prefs'
import { STRINGS, isLang, translate } from './translate'

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (key: string, vars?: Record<string, string | number>) => string; status: (key: string) => string }
/** In the sample a few ui.* texts are replaced by ui.demo.alt.<rest> (e.g. "saved" wording: nothing is saved there). */
const demoKey = (key: string) => {
  if (!key.startsWith('ui.')) return key
  // hosted-sample build only (a build-time constant): texts that promise uploading or reading the visitor's own document get a true wording, ui.hosted.alt.<rest>
  if (DEMO_ONLY && STRINGS.en[`ui.hosted.alt.${key.slice(3)}`]) return `ui.hosted.alt.${key.slice(3)}`
  if (typeof window === 'undefined' || !isDemoPath(window.location.pathname)) return key
  const alt = `ui.demo.alt.${key.slice(3)}`
  return STRINGS.en[alt] ? alt : key
}

const I18nContext = createContext<Ctx | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = readPref('language')
    return isLang(saved) ? saved : 'en'
  })
  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])
  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    writePref('language', l)
  }, [])
  const value = useMemo<Ctx>(
    () => ({ lang, setLang, t: (key, vars) => translate(lang, demoKey(key), vars), status: (key) => STRINGS[lang]?.[key]?.review_status ?? 'not_required' }),
    [lang, setLang],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useT(): Ctx {
  const c = useContext(I18nContext)
  if (!c) throw new Error('useT needs I18nProvider')
  return c
}
