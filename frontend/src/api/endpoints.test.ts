import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
// @ts-expect-error plain .mjs without types
import { generate, OUT, SPEC } from '../../scripts/gen-api-types.mjs'

const spec = JSON.parse(readFileSync(SPEC, 'utf8'))
const lf = (s: string) => s.replace(/\r\n/g, '\n')

describe('API contract', () => {
  it('openapi.generated.ts is up to date with docs/openapi.json (run: node scripts/gen-api-types.mjs)', () => {
    expect(lf(readFileSync(OUT, 'utf8'))).toBe(lf(generate(spec)))
  })
  it('every endpoint the client calls exists in openapi.json with the same method, and every v1 endpoint is wrapped', () => {
    const src = readFileSync(join(__dirname, 'endpoints.ts'), 'utf8')
    const norm = (p: string) => p.replace(/\$\{[^}]+\}|\{[^}]+\}/g, '{x}')
    const have = new Set<string>(Object.entries(spec.paths).flatMap(([p, m]) => Object.keys(m as object).map((k) => `${k.toUpperCase()} ${norm(p)}`)))
    const calls = [...src.matchAll(/=> api<.*>\(`\$\{V\}([^`]*)`(?:, \{ method: '(\w+)')?/g)].map((c) => {
      const path = c[1].replace(/\$\{q\([^}]*\}\)\}$/, '').replace(/\$\{q\(.*\)\}$/, '')
      return `${(c[2] ?? 'GET').toUpperCase()} /api/v1${norm(path)}`
    })
    expect(calls.length).toBe(23)
    expect(calls.filter((c) => !have.has(c))).toEqual([])
    expect([...have].filter((h) => h.includes('/api/v1') && !calls.includes(h))).toEqual([])
  })
})
