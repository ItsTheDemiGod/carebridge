/* Phase 7b write-up screenshots of /how-we-tested-it (static page, no backend). Needs the preview server on 4173 serving the current build.
 *   node scripts/screenshots7b.mjs ../docs/screenshots/phase7b [quality] */
import { chromium } from '@playwright/test'
import { mkdirSync, statSync } from 'node:fs'

const out = process.argv[2] ?? '../docs/screenshots/phase7b'
const q = Number(process.argv[3] ?? 74)
mkdirSync(out, { recursive: true })
const browser = await chromium.launch()

async function shot(lang, w, h, name, scrollTo) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, reducedMotion: 'reduce', deviceScaleFactor: 1 })
  await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
  await ctx.route('**/api/**', (r) => r.abort())
  const p = await ctx.newPage()
  await p.goto('http://localhost:4173/how-we-tested-it')
  await p.locator('tr[data-figure]').first().waitFor()
  await p.evaluate(() => document.fonts.ready)
  if (scrollTo) await p.locator(scrollTo).first().evaluate((el) => el.scrollIntoView({ block: 'start' }))
  await p.waitForTimeout(500)
  const file = `${out}/${name}.jpg`
  await p.screenshot({ path: file, type: 'jpeg', quality: q })
  console.log(name, Math.round(statSync(file).size / 1024) + ' KB')
  await ctx.close()
}

await shot('en', 1440, 900, 'testing-en-1440-top', '.tfinal')
await shot('en', 1440, 900, 'testing-en-1440-flags', '#tt-flags')
await shot('en', 390, 844, 'testing-en-390-top', '.tfinal')
await shot('en', 390, 844, 'testing-en-390-card', 'tr[data-figure="t_wrongsched"]')
await shot('ta', 1440, 900, 'testing-ta-1440', '.tfinal')
await shot('hi', 1440, 900, 'testing-hi-1440', '.tfinal')
await browser.close()
