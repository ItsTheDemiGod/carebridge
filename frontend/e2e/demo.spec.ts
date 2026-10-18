import { API } from './helpers'
import AxeBuilder from '@axe-core/playwright'
import { expect, test, type BrowserContext, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { card, pickDrug, watchErrors } from './flowhelpers'

/* Phase 6d: the pre-recorded sample (/demo). No backend is mocked and none is needed: the sample must make ZERO requests to /api. */
const STR = JSON.parse(readFileSync(fileURLToPath(new URL('../src/i18n/strings.generated.json', import.meta.url)), 'utf8')) as Record<string, Record<string, { text: string }>>
const LANGS = ['en', 'ta', 'hi'] as const
const LABEL = (l: string) => STR[l]['ui.demo.label'].text
const NOTE = (l: string) => STR[l]['ui.demo.prerecorded_note'].text
const ROUTES = ['/demo', '/demo/review', '/demo/result', '/demo/schedule', '/demo/summary']
const READY: Record<string, string> = { '/demo': '.steps-list', '/demo/review': 'article.med-card', '/demo/result': '.res-section', '/demo/schedule': '.slot', '/demo/summary': '.summary-table' }

/** every request the page makes, with /api calls aborted (so a stray one is both recorded and visible as a failure) */
function trackApi(ctx: BrowserContext | Page) {
  const api: string[] = []
  const all: string[] = []
  void ctx.route(API, (r) => {
    api.push(r.request().method() + ' ' + r.request().url())
    return r.abort()
  })
  const page = ctx as Page
  if (typeof page.on === 'function') page.on('request', (r) => all.push(r.url()))
  return { api, all }
}
const start = (c: BrowserContext, lang: string) => c.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)

/** the picker path on the flagged row, an acknowledgement, then Save */
async function walkReview(page: Page, lang: string) {
  const c0 = card(page, 0)
  await c0.locator('input[type=radio]').nth(1).check() // "choose the right medicine from the list"
  const box = c0.getByRole('combobox') // no preselection: the person types and chooses
  await box.fill('metf')
  await c0.getByRole('option').filter({ hasText: 'Metformin' }).first().waitFor()
  await box.press('ArrowDown')
  await box.press('Enter')
  await c0.locator('input[id*="-st-"]').first().check()
  for (const cb of await c0.locator('input[type=checkbox]').all()) await cb.check()
  await c0.locator('button.btn-primary').last().click()
  await page.locator('.rv-bar button.btn-primary').click()
  await expect(page.locator('.saved-panel')).toBeVisible()
  await expect(page.locator('.demo-note')).toHaveText(NOTE(lang))
}

for (const lang of LANGS) {
  test(`the whole sample walk makes zero requests to /api, stores nothing, and keeps the label on every page (${lang})`, async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 900 } })
    await start(ctx, lang)
    const page = await ctx.newPage()
    const { api, all } = trackApi(page)
    const errors = watchErrors(page)
    await page.goto('/demo')
    await expect(page.locator('.demo-strip')).toContainText(LABEL(lang))
    await expect(page.locator('.sample-tag')).toBeVisible()
    await page.locator('a[href="/demo/review"]').click()
    await page.locator('article.med-card').first().waitFor()
    await expect(page.locator('.demo-strip')).toContainText(LABEL(lang))
    await expect(page.locator('.delete-btn')).toHaveCount(0) // nothing to delete: the bar says so
    await walkReview(page, lang)
    await page.locator('a[href="/demo/result"]').click()
    await page.locator('.res-section').first().waitFor()
    await expect(page.locator('.demo-strip')).toContainText(LABEL(lang))
    await expect(page.locator('.demo-note')).toHaveText(NOTE(lang))
    for (const l of LANGS) {
      await page.locator(`[role=tab][lang=${l}]`).click()
      await expect(page.locator(`[role=tab][lang=${l}]`)).toHaveAttribute('aria-selected', 'true')
      await expect(page.locator('.res-section').first()).toBeVisible()
    }
    await page.locator('a[href="/demo/schedule"]').click()
    await page.locator('.slot').first().waitFor()
    await expect(page.locator('.demo-strip')).toContainText(LABEL(lang))
    await page.locator('.slot button').first().click() // mark a dose (memory only)
    await page.locator('a[href="/demo/summary"]').click()
    await page.locator('.summary-table').waitFor()
    await expect(page.locator('.demo-strip')).toContainText(LABEL(lang))
    if (lang !== 'en') await expect(page.locator('.draft-note')).toBeVisible() // the machine-translation note stays on every page in ta/hi
    // nothing was sent to /api, and nothing was stored beyond the two preferences
    expect(api).toEqual([])
    expect(all.filter((u) => new URL(u).pathname.startsWith('/api'))).toEqual([])
    const store = await page.evaluate(() => ({ keys: Object.keys(localStorage).sort(), session: Object.keys(sessionStorage), cookie: document.cookie, idb: indexedDB.databases ? 'checked' : 'n/a' }))
    expect(store.keys.every((k) => k === 'carebridge.language' || k === 'carebridge.calm')).toBe(true)
    expect(store.session).toEqual([])
    expect(store.cookie).toBe('')
    expect(page.url()).not.toMatch(/[?#]/) // no ids, names or results in the URL
    expect(errors).toEqual([])
    await ctx.close()
  })
}

test('the sample keeps working with the backend stopped and the network offline after the first load', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage()
  const { api } = trackApi(page) // "backend stopped": every /api call would fail; none may be made
  await page.goto('/demo')
  await page.locator('.steps-list').waitFor()
  await page.waitForLoadState('networkidle')
  await ctx.setOffline(true)
  await page.locator('a[href="/demo/review"]').click()
  await page.locator('article.med-card').first().waitFor()
  await expect(page.locator('img[alt]').first()).toBeVisible() // the sample photo came from memory
  await walkReview(page, 'en')
  await page.locator('a[href="/demo/result"]').click()
  await page.locator('.res-section').first().waitFor()
  await page.locator('a[href="/demo/schedule"]').click()
  await page.locator('.slot').first().waitFor()
  expect(api).toEqual([])
  await ctx.close()
})

test('the picker path: nothing is preselected, a pick is needed, and Save returns the recorded result with the visible note', async ({ page }) => {
  trackApi(page)
  await page.goto('/demo/review')
  await card(page, 0).waitFor()
  await expect(page.getByText('2 still need your check')).toBeVisible()
  const c0 = card(page, 0)
  await c0.getByLabel('Choose the right medicine from the list').check()
  await expect(c0.getByRole('button', { name: 'Use this check' })).toBeDisabled()
  const box = c0.getByRole('combobox', { name: /Search medicine/ })
  await expect(box).toHaveValue('')
  await pickDrug(page, c0, 'metf', 'Metformin')
  await c0.getByLabel('500 mg', { exact: true }).check()
  for (const cb of await c0.locator('input[type=checkbox]').all()) await cb.check() // any acknowledgement the card asks for
  await c0.getByRole('button', { name: 'Use this check' }).click()
  await page.getByRole('button', { name: 'Save my checks' }).click()
  await expect(page.getByText('In this sample the result is pre-recorded and does not change with your choices.')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Your checks are noted for this walk-through' })).toBeVisible()
  await expect(page.getByText('Your checks are saved')).toHaveCount(0) // the sample never says anything is saved
  await page.getByRole('link', { name: /See results/ }).click()
  await expect(page.getByText('In this sample the result is pre-recorded and does not change with your choices.')).toBeVisible()
  await expect(page.getByText('Interaction data: DDInter (CC BY-NC-SA 4.0)').first()).toBeVisible() // attribution wherever the pairs are shown
})

test('the review page says why the sample photo looks blurry, above the photo viewer', async ({ page }) => {
  trackApi(page)
  await page.goto('/demo/review')
  await card(page, 0).waitFor()
  const note = page.locator('.rv-pane .demo-photo-note')
  await expect(note).toHaveText(/deliberately blurry scan/)
  const nb = (await note.boundingBox())!
  const vb = (await page.locator('.rv-pane .pv-frame, .rv-pane img').first().boundingBox())!
  expect(nb.y + nb.height).toBeLessThanOrEqual(vb.y)
})

test('leaving the sample forgets what was done in it (marks, saved state) and goes to the landing page', async ({ page }) => {
  trackApi(page)
  await page.goto('/demo/review')
  await card(page, 0).waitFor()
  await walkReview(page, 'en')
  await page.getByRole('link', { name: 'Leave the sample' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
  await page.getByRole('link', { name: 'Try a sample document' }).first().click()
  await page.getByRole('link', { name: 'Start the sample' }).click()
  await card(page, 0).waitFor()
  await expect(page.getByText('0 of 4 medicines checked')).toBeVisible() // fresh again
})

test('the sample label stays on screen while the page scrolls (sticky header), also at 390 px', async ({ page }) => {
  trackApi(page)
  for (const w of [1280, 390]) {
    await page.setViewportSize({ width: w, height: 800 })
    await page.goto('/demo/result')
    await page.locator('.res-section').first().waitFor()
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await expect(page.locator('.demo-strip')).toBeInViewport({ ratio: 1 })
    await expect(page.getByRole('link', { name: 'Leave the sample' })).toBeInViewport({ ratio: 1 })
  }
})

for (const lang of LANGS)
  for (const w of [320, 390])
    test(`no sideways page scroll on any sample page in ${lang} at ${w}px`, async ({ browser }) => {
      const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: w, height: 800 } })
      await start(ctx, lang)
      const page = await ctx.newPage()
      trackApi(page)
      const problems: string[] = []
      for (const path of ROUTES) {
        await page.goto(path)
        await page.locator(READY[path]).first().waitFor()
        await page.evaluate(() => document.fonts.ready)
        await page.waitForTimeout(250)
        const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
        if (over > 0) problems.push(`${path}: ${over}px`)
      }
      expect(problems).toEqual([])
      await ctx.close()
    })

test('a sample link is offered on the landing page, the start page and how it works', async ({ page }) => {
  for (const [path, where] of [['/', 'landing'], ['/start', 'start'], ['/how-it-works', 'how']] as const) {
    await page.route(API, (r) => r.abort())
    await page.goto(path)
    const link = page.getByRole('link', { name: 'Try a sample document' })
    await expect(link.first(), where).toBeVisible()
    await expect(link.first()).toHaveAttribute('href', '/demo')
  }
})

test('when the service cannot be reached, /start, /consent and /privacy offer the sample (network failure and 502)', async ({ page }) => {
  for (const mode of ['abort', '502'] as const) {
    await page.unroute(API).catch(() => {})
    await page.route(API, (r) => (mode === 'abort' ? r.abort() : r.fulfill({ status: 502, contentType: 'text/plain', body: 'Bad gateway' })))
    for (const path of ['/start', '/consent', '/privacy']) {
      await page.goto(path)
      const link = page.getByRole('link', { name: 'Try a sample document' })
      await expect(link.first(), `${mode} ${path}`).toBeVisible()
      await link.first().click()
      await expect(page).toHaveURL(/\/demo$/)
      await expect(page.locator('.demo-strip')).toBeVisible()
    }
  }
})

test('keyboard: the sample can be started, the picker driven and Save pressed without a mouse; focus lands on the page heading', async ({ page }) => {
  trackApi(page)
  await page.goto('/demo')
  const startLink = page.getByRole('link', { name: 'Start the sample' })
  await startLink.focus()
  await page.keyboard.press('Enter')
  await card(page, 0).waitFor()
  await expect(page.getByRole('heading', { level: 1, name: 'Check your medicines' })).toBeFocused()
  const c0 = card(page, 0)
  await c0.getByLabel('Choose the right medicine from the list').focus()
  await page.keyboard.press('Space')
  const box = c0.getByRole('combobox', { name: /Search medicine/ })
  await box.focus()
  await page.keyboard.type('metf')
  await expect(c0.getByRole('option', { name: /Metformin/ })).toBeVisible()
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')
  await expect(c0.getByText('Metformin').first()).toBeVisible()
  const save = page.getByRole('button', { name: 'Save my checks' })
  await save.focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('.saved-panel')).toBeVisible()
  // the way out is reachable by keyboard too
  const leave = page.getByRole('link', { name: 'Leave the sample' })
  await leave.focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/$/)
})

test('the sample reads from the committed fixtures: the first screen shows the recorded medicines and the garbled name', async ({ page }) => {
  trackApi(page)
  await page.goto('/demo/review')
  await card(page, 0).waitFor()
  await expect(card(page, 0).getByText('Netfornin').first()).toBeVisible()
  await expect(card(page, 0).getByText('Needs your check')).toBeVisible()
})

/* axe on every sample route, in en, ta and hi, at desktop and 390 px */
for (const lang of LANGS)
  for (const w of [1280, 390])
    for (const path of ROUTES)
      test(`axe sample: ${path} in ${lang} at ${w}px`, async ({ browser }) => {
        const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: w, height: 900 } })
        await start(ctx, lang)
        const page = await ctx.newPage()
        trackApi(page)
        await page.goto(path)
        await page.locator(READY[path]).first().waitFor()
        await page.waitForTimeout(400)
        const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
        const lines = r.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}: ${v.nodes[0].target.join(' ')}`)
        expect(lines).toEqual([])
        await ctx.close()
      })
