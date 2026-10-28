import AxeBuilder from '@axe-core/playwright'
import { expect, test, type BrowserContext, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

/* Phase 8a: the hosted-sample build (vite --mode pages) served under /carebridge/ by a Pages-like server, with NO backend. Paths are relative to the base URL. */
const STR = JSON.parse(readFileSync(fileURLToPath(new URL('../src/i18n/strings.generated.json', import.meta.url)), 'utf8')) as Record<string, Record<string, { text: string }>>
const LANGS = ['en', 'ta', 'hi'] as const
const PUBLIC = ['', 'how-it-works', 'privacy', 'how-we-tested-it', 'demo', 'demo/review', 'demo/result', 'demo/schedule', 'demo/summary']
const REAL = ['start', 'consent', 'upload', 'documents', 'd/abc/review', 'd/abc/processing']
const ALL = [...PUBLIC, ...REAL, 'no-such-page']
const ORIGIN = 'http://localhost:4174'
const goto = (page: Page, route: string) => page.goto(route === '' ? './' : route)
const lang = async (ctx: BrowserContext, l: string) => ctx.addInitScript((x) => localStorage.setItem('carebridge.language', x), l)

/** Every request and console problem of a page. */
function watch(page: Page) {
  const requests: string[] = []
  const bad: string[] = []
  const errors: string[] = []
  page.on('request', (r) => requests.push(r.url()))
  page.on('response', (r) => {
    const req = r.request()
    if (r.status() >= 400 && req.resourceType() !== 'document') bad.push(`${r.status()} ${r.url()}`) // only the Pages 404.html document fallback may carry a 404
  })
  page.on('console', (m) => m.type() === 'error' && errors.push(`console: ${m.text()}`))
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
  return { requests, bad, errors }
}
const heading = (page: Page, route: string, l: string) => {
  if (REAL.includes(route)) return STR[l]['ui.hosted.title'].text
  return null
}

for (const l of LANGS)
  for (const route of ALL)
    test(`${l} /${route}: renders, no console errors, zero /api requests, only the Pages host, assets 200, deep link survives a reload`, async ({ browser }) => {
      const ctx = await browser.newContext({ reducedMotion: 'reduce' })
      await lang(ctx, l)
      const page = await ctx.newPage()
      const w = watch(page)
      await goto(page, route)
      const h1 = page.locator('main h1').first()
      await expect(h1).toBeVisible()
      const text = await h1.innerText()
      const want = heading(page, route, l)
      if (want) expect(text).toBe(want) // every real-flow route is the sample-only page
      await page.evaluate(() => document.fonts.ready)
      await page.reload() // a deep link and a reload are answered by 404.html and still reach the router
      await expect(page.locator('main h1').first()).toHaveText(text)
      expect(w.requests.filter((u) => /\/api(\/|$)/.test(new URL(u).pathname))).toEqual([])
      expect(w.requests.filter((u) => new URL(u).origin !== ORIGIN && !u.startsWith('data:'))).toEqual([]) // fonts, photos and fixtures are all self-hosted
      expect(w.bad).toEqual([])
      // a deep link is a document answered by 404.html with status 404 (how Pages does it); the browser logs that one status line per load. Asset 404s are caught by w.bad above.
      const docs404 = (m: string) => route !== '' && m === 'console: Failed to load resource: the server responded with a status of 404 (Not Found)'
      expect(w.errors.filter((m) => !docs404(m)).length).toBe(0)
      expect(w.errors.filter(docs404).length).toBeLessThanOrEqual(2)
      if (l === 'en') await expect(page.locator('.draft-note')).toHaveCount(0)
      else await expect(page.locator('.draft-note')).toBeVisible() // the persistent draft note in Tamil and Hindi
      await ctx.close()
    })

for (const l of LANGS)
  for (const w of [360, 390, 768, 1280, 1920])
    test(`${l} at ${w}px: no horizontal overflow on any route`, async ({ browser }) => {
      const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: w, height: 900 } })
      await lang(ctx, l)
      const page = await ctx.newPage()
      for (const route of ALL) {
        await goto(page, route)
        await page.locator('main h1').first().waitFor()
        await page.evaluate(() => document.fonts.ready)
        expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth), `/${route} at ${w}px`).toBeLessThanOrEqual(0)
      }
      await ctx.close()
    })

for (const l of LANGS)
  for (const w of [1280, 390])
    test(`axe: every route in ${l} at ${w}px`, async ({ browser }) => {
      const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: w, height: 900 } })
      await lang(ctx, l)
      const page = await ctx.newPage()
      for (const route of ALL) {
        await goto(page, route)
        await page.locator('main h1').first().waitFor()
        await page.evaluate(() => document.fonts.ready)
        const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
        expect(r.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}: ${v.nodes[0].target.join(' ')}`), `/${route}`).toEqual([])
      }
      await ctx.close()
    })

test('static files under the base path: manifest, icons, favicon, sample image all return 200 and the manifest points under the base', async ({ request }) => {
  for (const f of ['manifest.webmanifest', 'favicon.svg', 'favicon-32.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'demo/sample-document.png', '404.html']) expect((await request.get(f)).status(), f).toBe(200)
  expect((await request.get('no-such-file.xyz')).status()).toBe(404) // like Pages: 404.html with status 404
  const html = await (await request.get('./')).text()
  expect(html).toContain('/carebridge/assets/') // assets resolve under the base path
  expect(html).toContain('href="/carebridge/favicon.svg"')
})

test('the header shows only routes that exist here; the sample is the primary call to action; the landing page says it is a hosted sample', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await goto(page, '')
  const hrefs = await page.locator('header a').evaluateAll((a) => a.map((x) => x.getAttribute('href')))
  expect(hrefs.filter((h) => /\/(start|documents|consent|upload)$/.test(h ?? ''))).toEqual([])
  await expect(page.locator('header .nav-start')).toHaveText(STR.en['ui.demo.try'].text)
  await expect(page.locator('.hero-actions a').first()).toHaveText(STR.en['ui.demo.try'].text)
  await expect(page.locator('.hosted-note')).toHaveText(STR.en['ui.hosted.landing_note'].text)
  await expect(page.locator('header button[aria-label*="delete" i]')).toHaveCount(0)
})

test('the sample and the Testing page keep working offline after the first load (no network needed for navigation inside the app)', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()
  await goto(page, 'demo') // the intro loads the fixtures and the sample photo
  await expect(page.locator('main h1').first()).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  await ctx.setOffline(true)
  await page.locator('main').getByRole('link', { name: STR.en['ui.demo.intro.start'].text }).click()
  await expect(page).toHaveURL(/\/carebridge\/demo\/review$/)
  await expect(page.locator('main h1').first()).toBeVisible()
  await page.locator('.site-nav').getByRole('link', { name: STR.en['ui.nav.testing'].text }).click().catch(async () => {
    await page.getByRole('button', { name: STR.en['ui.nav.menu'].text }).click()
    await page.locator('.site-nav').getByRole('link', { name: STR.en['ui.nav.testing'].text }).click()
  })
  await expect(page).toHaveURL(/\/carebridge\/how-we-tested-it$/)
  await expect(page.locator('tr[data-figure]').first()).toBeVisible()
  await expect(page.locator('tr[data-sfigure]').first()).toBeVisible()
  await ctx.close()
})

test('localStorage holds only carebridge.language and carebridge.calm; no session storage, IndexedDB or cookies', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()
  for (const r of ['', 'demo', 'demo/review', 'demo/result', 'privacy', 'how-we-tested-it', 'start']) {
    await goto(page, r)
    await page.locator('main h1').first().waitFor()
  }
  await page.locator('.calm-toggle').click({ timeout: 5000 }) // before the language switch: Tamil needs a wider screen for the one-row header
  await page.locator('.lang-switch button[lang="ta"]').click({ timeout: 5000 })
  const s = await page.evaluate(async () => ({ local: Object.keys(localStorage).sort(), session: Object.keys(sessionStorage), idb: indexedDB.databases ? (await indexedDB.databases()).length : 0 }))
  expect(s.local.every((k) => ['carebridge.language', 'carebridge.calm'].includes(k))).toBe(true)
  expect(s.session).toEqual([])
  expect(s.idb).toBe(0)
  expect(await ctx.cookies()).toEqual([])
  await ctx.close()
})

test('the sample works end to end in the hosted build (intro, review, save, result)', async ({ page }) => {
  const w = watch(page)
  await page.setViewportSize({ width: 1440, height: 900 })
  await goto(page, 'demo')
  await page.locator('main').getByRole('link', { name: STR.en['ui.demo.intro.start'].text }).click()
  await expect(page).toHaveURL(/\/carebridge\/demo\/review$/)
  await expect(page.getByText(STR.en['ui.demo.label'].text, { exact: false }).first()).toBeVisible()
  expect(w.requests.filter((u) => /\/api(\/|$)/.test(new URL(u).pathname))).toEqual([])
  expect(w.errors.filter((m) => !m.includes('status of 404'))).toEqual([]) // the one 404 line is the deep-link document served as 404.html, as on Pages
})

test('hosted wording: no promise to upload, process a photo or read the visitor\'s own document; no claim that nothing is sent anywhere', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 900 } })
  const page = await ctx.newPage()
  await goto(page, '')
  await expect(page.locator('.hero .lede')).toHaveText(STR.en['ui.hosted.alt.hero.sub'].text)
  const promises = ['Upload a photo of a prescription', 'You upload a photo', 'Take a clear photo', 'Your photo is read on this computer', 'Nothing is sent to external services', 'We list each medicine we found', 'Get a short explanation', 'Start with a photo']
  for (const route of ['', 'how-it-works', 'privacy']) {
    await goto(page, route)
    await page.locator('main h1').first().waitFor()
    const text = await page.locator('main').innerText()
    for (const p of promises) expect(text, `/${route} contains "${p}"`).not.toContain(p)
    expect(text).not.toMatch(/nothing at all|nothing is sent anywhere|nothing is requested/i)
  }
  await ctx.close()
})
