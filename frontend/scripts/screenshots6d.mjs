/* Phase 6d screenshots (sample mode, testing page, landing). Needs the preview server on 4173 serving the current build.
 *   node scripts/screenshots6d.mjs ../docs/screenshots/phase6d [quality]
 * Everything is the pre-recorded sample or static pages: no backend, no model. */
import { chromium } from '@playwright/test'
import { mkdirSync, statSync } from 'node:fs'

const out = process.argv[2] ?? '../docs/screenshots/phase6d'
const q = Number(process.argv[3] ?? 74)
mkdirSync(out, { recursive: true })
const base = 'http://localhost:4173'
const browser = await chromium.launch()

async function shot(lang, w, h, path, name, steps, full = false) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, reducedMotion: 'reduce', deviceScaleFactor: 1 })
  await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
  await ctx.route('**/api/**', (r) => r.abort())
  const p = await ctx.newPage()
  await p.goto(base + path)
  await steps?.(p)
  await p.evaluate(() => document.fonts.ready)
  await p.waitForTimeout(500)
  const file = `${out}/${name}.jpg`
  await p.screenshot({ path: file, type: 'jpeg', quality: q, fullPage: full })
  console.log(name, Math.round(statSync(file).size / 1024) + ' KB')
  await ctx.close()
}

const reviewReady = (p) => p.locator('article.med-card').first().waitFor()
const pickMetformin = async (p) => {
  const c = p.locator('article.med-card', { has: p.locator('#rv-h-0') })
  await c.locator('input[type=radio]').nth(1).check()
  const box = c.getByRole('combobox')
  await box.fill('metf')
  await c.getByRole('option').filter({ hasText: 'Metformin' }).first().waitFor()
  await box.press('ArrowDown')
  await box.press('Enter')
  await c.locator('input[id*="-st-"]').first().check()
  for (const cb of await c.locator('input[type=checkbox]').all()) await cb.check()
  await c.locator('button.btn-primary').last().click()
}

await shot('en', 1440, 900, '/demo', 'demo-intro-1440', (p) => p.locator('.steps-list').waitFor())
await shot('en', 390, 844, '/demo', 'demo-intro-390', (p) => p.locator('.steps-list').waitFor(), true)
await shot('en', 1440, 900, '/demo/review', 'demo-review-before-1440', async (p) => { await reviewReady(p); await p.locator('article.med-card').first().scrollIntoViewIfNeeded(); await p.evaluate(() => window.scrollTo(0, 380)) })
await shot('en', 1440, 900, '/demo/review', 'demo-review-after-1440', async (p) => { await reviewReady(p); await pickMetformin(p); await p.evaluate(() => window.scrollTo(0, 380)) })
await shot('en', 390, 844, '/demo/review', 'demo-review-before-390', async (p) => { await reviewReady(p); await p.evaluate(() => window.scrollTo(0, 520)) })
await shot('en', 390, 844, '/demo/review', 'demo-review-after-390', async (p) => { await reviewReady(p); await pickMetformin(p); await p.evaluate(() => window.scrollTo(0, 560)) })
for (const lang of ['en', 'ta', 'hi']) {
  await shot(lang, 1440, 900, '/demo/review', `demo-result-${lang}-1440`, async (p) => {
    await reviewReady(p)
    await pickMetformin(p)
    await p.locator('.rv-bar button.btn-primary').click()
    await p.locator('.saved-panel').waitFor()
    await p.locator('a[href="/demo/result"]').click()
    await p.locator('.res-section').first().waitFor()
    await p.evaluate(() => window.scrollTo(0, 260))
  })
}
await shot('en', 1440, 900, '/how-we-tested-it', 'testing-en-1440', async (p) => { await p.locator('tr[data-figure]').first().waitFor(); await p.evaluate(() => window.scrollTo(0, 780)) })
await shot('en', 390, 844, '/how-we-tested-it', 'testing-en-390', async (p) => { await p.locator('tr[data-figure]').first().waitFor(); await p.evaluate(() => window.scrollTo(0, 900)) })
await shot('ta', 1440, 900, '/how-we-tested-it', 'testing-ta-1440', async (p) => { await p.locator('tr[data-figure]').first().waitFor(); await p.evaluate(() => window.scrollTo(0, 700)) })
await shot('en', 1440, 900, '/', 'landing-1440', (p) => p.locator('.hero-actions').waitFor())
await browser.close()
