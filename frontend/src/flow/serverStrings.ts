/* Backend-owned fixed text (error., job., confirm., picker., schedule., summary., delete., label., heading., timing., banner., notice.).
 * Fetched once per language from GET /strings and kept in memory only. The frontend never duplicates these strings. */
import { useEffect, useState } from 'react'
import { strings } from '../api/endpoints'
import type { Lang } from '../api/types'
import { useT } from '../i18n/I18n'

const cache = new Map<Lang, Record<string, string>>()
const inflight = new Map<Lang, Promise<Record<string, string>>>()

export function loadServerStrings(lang: Lang): Promise<Record<string, string>> {
  const hit = cache.get(lang)
  if (hit) return Promise.resolve(hit)
  let p = inflight.get(lang)
  if (!p) {
    p = strings(lang)
      .then((r) => (cache.set(lang, r.strings), r.strings))
      .finally(() => inflight.delete(lang))
    inflight.set(lang, p)
  }
  return p
}

export const fill = (text: string, vars?: Record<string, string | number>) => (vars ? text.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : text)

export function useServerStrings() {
  const { lang } = useT()
  const [table, setTable] = useState<Record<string, string> | null>(cache.get(lang) ?? null)
  useEffect(() => {
    let live = true
    setTable(cache.get(lang) ?? null)
    loadServerStrings(lang)
      .then((t) => live && setTable(t))
      .catch(() => live && setTable({}))
    return () => {
      live = false
    }
  }, [lang])
  /** the backend text for a template id, or `fallback` when it is not (yet) loaded */
  const s = (id: string, vars?: Record<string, string | number>, fallback = ''): string => {
    const t = table?.[id]
    return t === undefined ? fallback : fill(t, vars)
  }
  return { s, ready: table !== null }
}

/** Test helper. */
export const _clearServerStringCache = () => cache.clear()
