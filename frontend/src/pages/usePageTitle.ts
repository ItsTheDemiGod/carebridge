import { useEffect } from 'react'
import { useT } from '../i18n/I18n'

/** Sets document.title from a ui.title.* string and follows the selected language. */
export function usePageTitle(key: string) {
  const { t, lang } = useT()
  useEffect(() => {
    document.title = t(key)
  }, [key, lang, t])
}
