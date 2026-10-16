import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Lang } from '../api/client'
import { readPref, writePref } from '../lib/prefs'
import { STRINGS, isLang, translate } from './translate'

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (key: string, vars?: Record<string, string | number>) => string; status: (key: string) => string }
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
    () => ({ lang, setLang, t: (key, vars) => translate(lang, key, vars), status: (key) => STRINGS[lang]?.[key]?.review_status ?? 'not_required' }),
    [lang, setLang],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useT(): Ctx {
  const c = useContext(I18nContext)
  if (!c) throw new Error('useT needs I18nProvider')
  return c
}
