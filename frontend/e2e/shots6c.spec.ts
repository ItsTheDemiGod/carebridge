/* Phase 6c screenshots (mocked fixtures, dev document image from data/rendered when present). Not part of the normal run:
 *   $env:SHOTS=1; npx playwright test e2e/shots6c.spec.ts   (the preview server on port 4173 must serve the current build) */
import { expect, test, type Page } from '@playwright/test'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { DOC_ID, card, openCard, reviewReady, setLangInit } from './flowhelpers'

const OUT = fileURLToPath(new URL('../../docs/screenshots/phase6c/', import.meta.url))
const IMG = fileURLToPath(new URL('../../data/rendered/clean/ds_037.png', import.meta.url))
test.skip(!process.env.SHOTS, 'screenshots are taken on request (SHOTS=1)')
mkdirSync(OUT, { recursive: true })

async function reveal(page: Page) {
  for (let y = 0; y < 9000; y += 450) {
    await page.evaluate((v) => window.scrollTo(0, v), y)
    await page.waitForTimeout(90)
  }
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(400)
}

/** JPEG under about 290 KB: lower the quality until it fits */
async function shot(page: Page, name: string, full = false) {
  await page.addStyleTag({ content: '.cursor-ring, .cursor-dot { display: none !important }' }) // the pointer ring is not part of the page
  let buf = Buffer.alloc(0)
  for (const q of [60, 50, 40, 32, 25, 18, 12]) {
    buf = await page.screenshot({ type: 'jpeg', quality: q, fullPage: full })
    if (buf.length < 290_000) break
  }
  writeFileSync(`${OUT}${name}.jpg`, buf)
  expect(buf.length).toBeLessThan(300_000)
}

const common = async (page: Page, lang: string, w: number, h: number) => {
  await page.setViewportSize({ width: w, height: h })
  await setLangInit(page, lang)
  await reviewReady(page, { imageKept: true, imageBody: existsSync(IMG) ? readFileSync(IMG) : undefined })
}

for (const [lang, w] of [['en', 390], ['en', 768], ['en', 1440], ['ta', 1440], ['hi', 1440]] as const)
  test(`landing ${lang} ${w}`, async ({ page }) => {
    await common(page, lang, w, 900)
    await page.goto('/')
    await page.locator('h1').waitFor()
    await reveal(page)
    await shot(page, `landing_${lang}_${w}`, true)
  })

for (const [w, h] of [[1440, 900], [390, 844]] as const)
  test(`review ${w}`, async ({ page }) => {
    await common(page, 'en', w, h)
    await page.goto(`/d/${DOC_ID}/review`)
    await card(page, 1).waitFor()
    await page.waitForTimeout(1200)
    const y = w > 1000 ? 330 : 520
    await page.evaluate((v) => window.scrollTo(0, v), y)
    await page.waitForTimeout(900)
    await shot(page, `review_${w}_before`)
    const c = await openCard(page, 2)
    await c.getByLabel('This matches my document').check()
    await c.getByLabel(/I have checked how often/).check()
    await c.getByRole('button', { name: 'Use this check' }).click()
    await page.waitForTimeout(900)
    await shot(page, `review_${w}_after_one_check`)
  })

for (const w of [390, 1440])
  test(`how it works ${w}`, async ({ page }) => {
    await common(page, 'en', w, 900)
    await page.goto('/how-it-works')
    await page.locator('h1').waitFor()
    await reveal(page)
    await shot(page, `how_${w}`, true)
  })

for (const w of [390, 1440])
  test(`result ${w}`, async ({ page }) => {
    await common(page, 'en', w, 900)
    await page.goto(`/d/${DOC_ID}/result`)
    await page.locator('.res-section').first().waitFor()
    await reveal(page)
    await shot(page, `result_${w}`, true)
  })

for (const w of [1024, 1280])
  test(`header ${w}`, async ({ page }) => {
    await common(page, 'en', w, 300)
    await page.goto('/documents')
    await page.locator('h1').first().waitFor()
    await page.waitForTimeout(500)
    await page.screenshot({ path: `${OUT}header_${w}.jpg`, type: 'jpeg', quality: 70, clip: { x: 0, y: 0, width: w, height: 90 } })
  })

test('header 390 with the menu open', async ({ page }) => {
  await common(page, 'en', 390, 700)
  await page.goto('/documents')
  await page.locator('.menu-btn').click()
  await page.waitForTimeout(400)
  await shot(page, 'header_390_menu_open')
})
