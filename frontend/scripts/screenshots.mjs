// Takes full-page screenshots of the built site (vite preview must be running on :4173).
//   node scripts/screenshots.mjs <outDir> [quality]
// Scrolls through the page first so scroll reveals have fired, and lets the ambient layer settle.
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const out = process.argv[2] ?? 'shots'
const quality = Number(process.argv[3] ?? 60)
const BASE = process.env.BASE_URL ?? 'http://localhost:4173'
mkdirSync(out, { recursive: true })

const shots = [
  ['landing-390-en', '/', 390, 'en'],
  ['landing-768-en', '/', 768, 'en'],
  ['landing-1440-en', '/', 1440, 'en'],
  ['landing-1440-ta', '/', 1440, 'ta'],
  ['landing-1440-hi', '/', 1440, 'hi'],
  ['privacy-1440-en', '/privacy', 1440, 'en'],
  ['how-1440-en', '/how-it-works', 1440, 'en'],
]
const only = process.env.ONLY?.split(',')

const browser = await chromium.launch()
for (const [name, path, width, lang] of shots) {
  if (only && !only.includes(name)) continue
  const ctx = await browser.newContext({ viewport: { width, height: width < 600 ? 844 : 900 }, deviceScaleFactor: 1 })
  await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
  const page = await ctx.newPage()
  await page.goto(BASE + path, { waitUntil: 'networkidle' })
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) {
      window.scrollTo(0, y)
      await new Promise((r) => setTimeout(r, 120))
    }
    window.scrollTo(0, 0)
    await document.fonts.ready
  })
  await page.waitForTimeout(900)
  await page.screenshot({ path: `${out}/${name}.jpg`, type: 'jpeg', quality, fullPage: true })
  await ctx.close()
}
await browser.close()
