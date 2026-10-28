import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { blockApi } from './helpers'

/* Phase 7c-lite: the stress section of "How we tested it". Figures come only from src/data/testing.generated.json (key stress_ext). */
const read = (rel: string) => readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf8')
type Cell = { k: number | null; n: number | null; value: number | null; wilson: number[] | null; bootstrap: number[] | null }
type Fig = { id: string; group: string; source: string; split: string; date: string; cells: Record<string, Cell>; no_kn?: boolean; passed?: boolean }
const S = (JSON.parse(read('../src/data/testing.generated.json')) as { stress_ext: { run: boolean; date: string; conditions: string[]; entries: Fig[]; groups: string[] } }).stress_ext
const STR = JSON.parse(read('../src/i18n/strings.generated.json')) as Record<string, Record<string, { text: string }>>
const LANGS = ['en', 'ta', 'hi'] as const
const pct = (x: number) => `${(x * 100).toFixed(1)}%`
const FORBIDDEN = /\b(safe|safely|guaranteed?|accurate|accurately|accuracy|certified|clinically validated|doctor-approved|reliable|validated)\b/i

for (const lang of LANGS)
  test(`the stress section renders in ${lang}: every figure has its source, measure, data line, split label, interval and date`, async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: 'reduce' })
    await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
    const page = await ctx.newPage()
    await blockApi(page)
    await page.goto('/how-we-tested-it')
    const sec = page.locator('section.tstress')
    await expect(sec.getByRole('heading', { level: 2 })).toHaveText(STR[lang]['ui.testing.s.title'].text)
    const rows = sec.locator('tr[data-sfigure]')
    await expect(rows).toHaveCount(S.entries.length)
    expect(await rows.evaluateAll((r) => r.map((x) => x.getAttribute('data-sfigure')))).toEqual(S.entries.map((e) => e.id))
    for (const e of S.entries) {
      const row = sec.locator(`tr[data-sfigure="${e.id}"]`)
      for (const c of S.conditions) {
        const cell = row.locator(`td[data-cond="${c}"]`)
        const x = e.cells[c]
        await expect(cell.locator('strong')).toHaveText(pct(x.value as number)) // the shown figure is the file's figure, in Western digits
        if (!e.no_kn) await expect(cell).toContainText(`${x.k}`)
        if (x.wilson) await expect(cell.locator('.t-wilson')).toContainText(`[${pct(x.wilson[0])}, ${pct(x.wilson[1])}]`)
        if (x.bootstrap) await expect(cell.locator('.t-boot')).toContainText(`[${pct(x.bootstrap[0])}, ${pct(x.bootstrap[1])}]`)
        expect(x.wilson !== null || x.bootstrap !== null).toBe(true) // every figure carries an interval
      }
      await expect(row.locator('code.t-source')).toHaveText(e.source)
      expect(e.source).toMatch(/^eval\/results\/stress-extraction-v1\/metrics\.json$/)
      expect((await row.locator('td.t-measures').innerText()).trim().length).toBeGreaterThan(20)
      expect(e.split).toBe('stress')
      expect(e.date).toBe(S.date)
    }
    // data line, split label and run date once per group
    const lines = sec.locator('.group-data')
    await expect(lines).toHaveCount(S.groups.length)
    for (const t of await lines.allInnerTexts()) {
      expect(t).toContain(STR[lang]['ui.testing.split.stress'].text)
      expect(t).toContain(S.date)
    }
    // the four pre-registered limits and their results are shown, met or not
    for (const e of S.entries.filter((x) => x.group === 'crit'))
      await expect(sec.locator(`tr[data-sfigure="${e.id}"] th`)).toContainText(STR[lang][e.passed ? 'ui.testing.s.met' : 'ui.testing.s.notmet'].text)
    // the unfavourable figures are there, not hidden
    await expect(sec.locator('tr[data-sfigure="unconf"] td[data-cond="clean"] strong')).not.toHaveText(pct(0))
    await expect(sec.locator('tr[data-sfigure="garbled"] td[data-cond="photo"] strong')).not.toHaveText(pct(1))
    // the version deviation is stated; the held-out section and the dev groups are still there
    await expect(sec.getByText(STR[lang]['ui.testing.s.deviation'].text.split('{')[0].trim(), { exact: false })).toBeVisible()
    await expect(page.locator('tr[data-figure]').first()).toBeVisible()
    if (lang !== 'en') await expect(page.locator('.draft-note')).toBeVisible()
    if (lang === 'en') expect(await sec.innerText()).not.toMatch(FORBIDDEN)
    await ctx.close()
  })

test('at 360 px the stress table reflows into labelled cards with no sideways scroll', async ({ page }) => {
  await blockApi(page)
  await page.setViewportSize({ width: 360, height: 800 })
  await page.goto('/how-we-tested-it')
  const first = page.locator('tr[data-sfigure]').first()
  await first.waitFor()
  await page.evaluate(() => document.fonts.ready)
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0)
  expect(await first.evaluate((r) => getComputedStyle(r).display)).toBe('block')
  expect(await first.locator('td').first().evaluate((c) => getComputedStyle(c, '::before').content)).not.toBe('none')
  await expect(page.locator('section.tstress .table-wrap').first()).toHaveAttribute('role', 'region')
})
