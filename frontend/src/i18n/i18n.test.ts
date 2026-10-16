import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import { STRINGS, translate } from './translate'

const SRC = join(__dirname, '..')
const files = (dir: string): string[] =>
  readdirSync(dir).flatMap((f) => {
    const p = join(dir, f)
    return statSync(p).isDirectory() ? files(p) : [p]
  })
const sources = files(SRC).filter((f) => /\.(tsx|ts)$/.test(f) && !/\.test\.ts$/.test(f))

describe('strings', () => {
  it('every key exists in all three languages with the same placeholders and a review status', () => {
    const en = Object.keys(STRINGS.en)
    expect(en.length).toBeGreaterThan(80)
    const ph = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort().join()
    for (const lang of ['ta', 'hi'] as const) {
      expect(Object.keys(STRINGS[lang]).sort()).toEqual([...en].sort())
      for (const k of en) {
        expect(ph(STRINGS[lang][k].text), `${lang} ${k}`).toBe(ph(STRINGS.en[k].text))
        expect(STRINGS[lang][k].review_status).toBe('draft_unreviewed')
      }
    }
  })

  it('every key used in the source exists', () => {
    const used = new Set<string>()
    for (const f of sources) for (const m of readFileSync(f, 'utf8').matchAll(/\bt\(\s*['"`](ui\.[\w.]+)['"`]/g)) used.add(m[1])
    expect(used.size).toBeGreaterThan(30)
    expect([...used].filter((k) => !(k in STRINGS.en))).toEqual([])
  })

  it('falls back to English for a missing key and fills placeholders', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const table = { en: { 'ui.a': { text: 'Hello {n}', review_status: 'not_required' } }, ta: {}, hi: {} }
    expect(translate('ta', 'ui.a', { n: 3 }, table)).toBe('Hello 3')
    expect(translate('hi', 'ui.zzz', undefined, table)).toBe('ui.zzz')
    expect(warn).toHaveBeenCalled()
    warn.mockRestore()
  })
})

/* Best-effort scan, NOT a proof. It looks for (1) text between a closing ">" and the next "<" in .tsx files and
 * (2) literal alt / aria-label / title / placeholder attribute values. It cannot see strings built in expressions,
 * template literals, or text inside non-JSX .ts files, and it ignores text with code characters. */
describe('no literal visible text in components', () => {
  const tsx = sources.filter((f) => f.endsWith('.tsx'))
  const strip = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1')
  it('finds no JSX text nodes with letters', () => {
    const found: string[] = []
    for (const f of tsx) {
      const code = strip(readFileSync(f, 'utf8'))
      for (const m of code.matchAll(/(?<![=-])>([^<>{}]+)</g)) {
        const text = m[1].trim()
        if (/[A-Za-zऀ-෿]/.test(text) && !/[;()=]/.test(text) && !/^[\w'"-]+:$/.test(text.split('\n').pop()!.trim()) && !/^[,\s]*$/.test(text)) found.push(`${f.replace(SRC, '')}: ${text.slice(0, 40)}`)
      }
    }
    expect(found).toEqual([])
  })
  it('finds no literal alt, aria-label, title or placeholder text', () => {
    const found: string[] = []
    for (const f of tsx) {
      const code = strip(readFileSync(f, 'utf8'))
      for (const m of code.matchAll(/\b(alt|aria-label|title|placeholder)="([^"]*[A-Za-z][^"]*)"/g)) found.push(`${f.replace(SRC, '')}: ${m[1]}="${m[2]}"`)
    }
    expect(found).toEqual([])
  })
})
