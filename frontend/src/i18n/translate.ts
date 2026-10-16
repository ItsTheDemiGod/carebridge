import generated from './strings.generated.json'
import type { Lang } from '../api/client'

export type StringEntry = { text: string; review_status: string }
export type Table = Record<Lang, Record<string, StringEntry>>
export const STRINGS = generated as Table
export const LANGS: { code: Lang; name: string }[] = [
  { code: 'en', name: 'English' },
  { code: 'ta', name: 'தமிழ்' },
  { code: 'hi', name: 'हिन्दी' },
]
export const isLang = (x: unknown): x is Lang => x === 'en' || x === 'ta' || x === 'hi'

/** Pure lookup: the key in `lang`, else English (logged in development only), else the key itself. */
export function translate(lang: Lang, key: string, vars?: Record<string, string | number>, table: Table = STRINGS): string {
  let text = table[lang]?.[key]?.text
  if (text === undefined) {
    if (import.meta.env.DEV) console.warn(`[i18n] missing key "${key}" for ${lang}`)
    text = table.en[key]?.text ?? key
  }
  return vars ? text.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : text
}
