import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { blockApi } from './helpers'

/* Phase 6d: the "How we tested it" page. Figures come only from src/data/testing.generated.json (scripts/build_testing_page_data.py). */
const read = (rel: string) => readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf8')
const DATA = JSON.parse(read('../src/data/testing.generated.json')) as { entries: { id: string; value: number; unit: string; source: string; n?: number; of?: number }[]; final_test: { run: boolean } }
const STR = JSON.parse(read('../src/i18n/strings.generated.json')) as Record<string, Record<string, { text: string }>>
const LANGS = ['en', 'ta', 'hi'] as const
const fmt = (e: { value: number; unit: string }) => (e.unit === 'ratio' ? `${(e.value * 100).toFixed(1)}%` : String(e.value))
const FORBIDDEN = /\b(safe|safely|guaranteed?|accurate|accurately|accuracy|certified|clinically validated|doctor-approved|reliable|validated)\b/i

for (const lang of LANGS)
  test(`the page renders in ${lang}: every figure has a source path and a measures text, and nothing appears that is not in the generated file`, async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: 'reduce' })
    await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
    const page = await ctx.newPage()
    await blockApi(page)
    await page.goto('/how-we-tested-it')
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(STR[lang]['ui.testing.title'].text)
    const rows = page.locator('tr[data-figure]')
    await expect(rows).toHaveCount(DATA.entries.length)
    expect(await rows.evaluateAll((r) => r.map((x) => x.getAttribute('data-figure')))).toEqual(DATA.entries.map((e) => e.id))
    for (const e of DATA.entries) {
      const row = page.locator(`tr[data-figure="${e.id}"]`)
      await expect(row.locator('.t-result strong')).toHaveText(fmt(e)) // the shown figure is the file's figure, in Western digits
      await expect(row.locator('code.t-source')).toHaveText(e.source) // every figure carries its committed source path
      expect((await row.locator('td.t-measures').innerText()).trim().length).toBeGreaterThan(20) // "what this measures"
      expect(e.source).toMatch(/^(eval\/results\/.+\/metrics\.json|docs\/smoke\/.+\.json)$/)
    }
    for (const th of await page.locator('tbody th').allInnerTexts()) expect(th).not.toContain('F1') // the score name lives only in the measures column
    await expect(page.locator('.group-data')).not.toHaveCount(0) // shared data line, once per group
    // the unit-less numbers stay Western digits in Tamil and Hindi too
    for (const t of await page.locator('.t-result strong').allInnerTexts()) expect(t).toMatch(/^[0-9.%]+$/)
    // held-out test results: stated as not yet run, never a number or placeholder
    expect(DATA.final_test.run).toBe(false)
    await expect(page.getByText(STR[lang]['ui.testing.final.not_run'].text)).toBeVisible()
    await expect(page.locator('tr[data-figure]', { hasText: STR[lang]['ui.testing.split.test'].text })).toHaveCount(0)
    // the Limits section is there, and names the points the brief lists
    const limits = page.locator('.tlimits')
    await expect(limits.getByRole('heading', { name: STR[lang]['ui.testing.limits.title'].text })).toBeVisible()
    await expect(limits.locator('li')).toHaveCount(7)
    if (lang !== 'en') await expect(page.locator('.draft-note')).toBeVisible()
    if (lang === 'en') expect(await page.locator('main').innerText()).not.toMatch(FORBIDDEN)
    await ctx.close()
  })

test('the header and the landing page link to the page', async ({ page }) => {
  await blockApi(page)
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/')
  await page.locator('.site-nav').getByRole('link', { name: STR.en['ui.nav.testing'].text }).click()
  await expect(page).toHaveURL(/\/how-we-tested-it$/)
  await page.goto('/')
  await page.getByRole('link', { name: STR.en['ui.testing.teaser_link'].text }).click()
  await expect(page).toHaveURL(/\/how-we-tested-it$/)
})

test('at 360 px there is no sideways page scroll and every figure is a card with its labels', async ({ page }) => {
  await blockApi(page)
  await page.setViewportSize({ width: 360, height: 800 })
  await page.goto('/how-we-tested-it')
  await page.locator('tr[data-figure]').first().waitFor()
  await page.evaluate(() => document.fonts.ready)
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0)
  const first = page.locator('tr[data-figure]').first()
  expect(await first.evaluate((r) => getComputedStyle(r).display)).toBe('block') // reflowed, not a squeezed table
  expect(await first.locator('td').first().evaluate((c) => getComputedStyle(c, '::before').content)).not.toBe('none')
  // the scroll container (used on wider screens) is a focusable, named region
  await expect(page.locator('.tgroup .table-wrap').first()).toHaveAttribute('tabindex', '0')
  await expect(page.locator('.tgroup .table-wrap').first()).toHaveAttribute('role', 'region')
})

for (const lang of LANGS)
  for (const w of [1280, 390])
    test(`axe: how we tested it in ${lang} at ${w}px`, async ({ browser }) => {
      const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: w, height: 900 } })
      await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
      const page = await ctx.newPage()
      await blockApi(page)
      await page.goto('/how-we-tested-it')
      await page.locator('tr[data-figure]').first().waitFor()
      await page.evaluate(() => document.fonts.ready)
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
      expect(r.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}: ${v.nodes[0].target.join(' ')}`)).toEqual([])
      await ctx.close()
    })
