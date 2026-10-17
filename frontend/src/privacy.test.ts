import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

/* Source scans for the browser-side privacy rules (docs/PRIVACY.md, "browser side"). Best effort, not a proof; the Playwright suite checks the running app. */
const SRC = __dirname
const files = (dir: string): string[] => readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? files(join(dir, f)) : [join(dir, f)]))
const code = files(SRC).filter((f) => /\.(ts|tsx)$/.test(f) && !/\.test\.ts$/.test(f))
const strip = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1')
const hits = (re: RegExp, except: RegExp | null = null) => code.filter((f) => re.test(strip(readFileSync(f, 'utf8'))) && !(except && except.test(f.replace(/\\/g, '/'))))

describe('browser-side privacy rules', () => {
  it('never uses dangerouslySetInnerHTML or innerHTML', () => {
    expect(hits(/dangerouslySetInnerHTML|\.innerHTML\s*=|insertAdjacentHTML/)).toEqual([])
  })
  it('only lib/prefs.ts touches localStorage; nothing uses sessionStorage, IndexedDB or document.cookie', () => {
    expect(hits(/localStorage/, /lib\/prefs\.ts$/)).toEqual([])
    expect(hits(/sessionStorage|indexedDB|document\.cookie|caches\.open|history\.(push|replace)State/)).toEqual([])
  })
  it('stores only language and calm mode', () => {
    const prefs = readFileSync(join(SRC, 'lib', 'prefs.ts'), 'utf8')
    expect([...prefs.matchAll(/'(carebridge\.[a-z]+)'/g)].map((m) => m[1]).sort()).toEqual(['carebridge.calm', 'carebridge.language'])
  })
  it('puts no query string on any in-app navigation and never logs', () => {
    expect(hits(/\bnav(?:igate)?\(\s*[`'"][^`'"]*\?/)).toEqual([])
    expect(hits(/console\.(log|info|debug)\(/, /perf|FrameMonitor/)).toEqual([])
  })
  it('has no external http(s) URL in the app code (nothing loads from the network)', () => {
    const bad = code.filter((f) => /https?:\/\/(?!localhost|127\.0\.0\.1|www\.w3\.org)/.test(strip(readFileSync(f, 'utf8'))))
    expect(bad).toEqual([])
  })
  it('index.html sends no referrer', () => {
    expect(readFileSync(join(SRC, '..', 'index.html'), 'utf8')).toContain('<meta name="referrer" content="no-referrer"')
  })
})
