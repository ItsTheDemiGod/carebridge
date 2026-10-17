import { expect, test } from '@playwright/test'
import { setLangInit } from './flowhelpers'
import { mockApi } from './mock'

const PUBLIC = ['/', '/how-it-works', '/privacy', '/no-such-page']
const LANGS = ['en', 'ta', 'hi'] as const

for (const lang of LANGS)
  test(`public routes are quiet in ${lang}: no console output, no failed or 4xx/5xx requests, no session call, title and description set`, async ({ page }) => {
    await setLangInit(page, lang)
    const mock = await mockApi(page)
    const noise: string[] = []
    page.on('console', (m) => ['error', 'warning'].includes(m.type()) && noise.push(`${m.type()}: ${m.text()}`))
    page.on('pageerror', (e) => noise.push(`pageerror: ${e.message}`))
    page.on('requestfailed', (r) => noise.push(`failed: ${r.url()}`))
    page.on('response', (r) => r.status() >= 400 && noise.push(`${r.status()}: ${r.url()}`))
    const seen = new Set<string>()
    for (const path of PUBLIC) {
      await page.goto(path, { waitUntil: 'networkidle' })
      await expect(page.locator('h1')).toBeVisible()
      const title = await page.title()
      const desc = await page.locator('meta[name=description]').getAttribute('content')
      expect(title.length, path).toBeGreaterThan(3)
      expect(desc?.length, path).toBeGreaterThan(10)
      expect(seen.has(title), `unique title for ${path}`).toBe(false)
      seen.add(title)
    }
    expect(mock.count('GET', '/api/v1/session'), 'no session call on public routes').toBe(0)
    expect(noise).toEqual([])
  })

test('favicon, touch icon and manifest all resolve (no 404 on any route)', async ({ page, request }) => {
  await page.goto('/')
  const hrefs = await page.locator('head link[rel~=icon], head link[rel=apple-touch-icon], head link[rel=manifest]').evaluateAll((l) => l.map((e) => (e as HTMLLinkElement).href))
  expect(hrefs.length).toBeGreaterThanOrEqual(4)
  for (const h of hrefs) expect((await request.get(h)).status(), h).toBe(200)
  const manifest = await (await request.get('/manifest.webmanifest')).json()
  for (const i of manifest.icons) expect((await request.get(i.src)).status(), i.src).toBe(200)
  expect(await page.locator('meta[name=theme-color]').getAttribute('content')).toBe('#f5efe3')
})
