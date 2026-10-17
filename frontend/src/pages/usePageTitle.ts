import { useEffect } from 'react'
import { useT } from '../i18n/I18n'

const META: Record<string, string> = { 'ui.title.home': 'ui.meta.home', 'ui.title.how': 'ui.meta.how', 'ui.title.privacy': 'ui.meta.privacy', 'ui.title.notfound': 'ui.meta.notfound' }

/** Sets document.title from a ui.title.* string and the meta description from ui.meta.*; both follow the selected language. */
export function usePageTitle(key: string) {
  const { t, lang } = useT()
  useEffect(() => {
    document.title = t(key)
    document.querySelector('meta[name="description"]')?.setAttribute('content', t(META[key] ?? 'ui.meta.flow'))
  }, [key, lang, t])
}
