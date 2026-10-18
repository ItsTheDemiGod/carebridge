import { expect, test, type Page } from '@playwright/test'
import { DOC_ID, PNG, reviewReady, setLangInit } from './flowhelpers'

const LANGS = ['en', 'ta', 'hi'] as const
const WIDTHS = [320, 360, 390, 768]

type Route = { name: string; go: (p: Page) => Promise<void>; ready: string }
const ROUTES: Route[] = [
  { name: 'landing', go: (p) => p.goto('/'), ready: 'h1' },
  { name: 'how-it-works', go: (p) => p.goto('/how-it-works'), ready: 'h1' },
  { name: 'privacy', go: (p) => p.goto('/privacy'), ready: 'h1' },
  { name: 'start', go: (p) => p.goto('/start'), ready: 'h1' },
  { name: 'consent', go: (p) => p.goto('/consent'), ready: '.purposes' },
  { name: 'upload', go: (p) => p.goto('/upload'), ready: '.dropzone' },
  {
    name: 'upload-preview',
    go: async (p) => {
      await p.goto('/upload')
      await p.locator('#file-pick').setInputFiles({ name: 'a.png', mimeType: 'image/png', buffer: PNG })
    },
    ready: '.preview img',
  },
  { name: 'documents', go: (p) => p.goto('/documents'), ready: 'h1' },
  { name: 'review', go: (p) => p.goto(`/d/${DOC_ID}/review`), ready: 'article.med-card' },
  { name: 'result', go: (p) => p.goto(`/d/${DOC_ID}/result`), ready: '.res-section' },
  { name: 'schedule', go: (p) => p.goto(`/d/${DOC_ID}/schedule`), ready: '.slot' },
  { name: 'summary', go: (p) => p.goto(`/d/${DOC_ID}/summary`), ready: '.summary-table' },
  { name: '404', go: (p) => p.goto('/no-such-page'), ready: 'h1' },
]

/** elements that are wider than the screen (ignoring things that are clipped on purpose) */
const wide = (p: Page) =>
  p.evaluate(() =>
    [...document.querySelectorAll('main *, header *, footer *')]
      .filter((e) => !e.closest('.sr-only, dialog:not([open]), [hidden], .pv-frame, .mosaic, .hero-art, svg, .table-wrap'))
      .filter((e) => {
        const r = e.getBoundingClientRect()
        const cs = getComputedStyle(e)
        return r.width > 0 && cs.visibility !== 'hidden' && r.right > window.innerWidth + 1
      })
      .slice(0, 4)
      .map((e) => `${e.tagName}.${(e.className?.toString() ?? '').slice(0, 30)}`),
  )

const targets = (p: Page) =>
  p.evaluate(() =>
    [...document.querySelectorAll('button, a.btn, .btn, .site-nav a, summary, [role=tab], label.btn, input[type=checkbox], input[type=radio], select')]
      .filter((e) => !e.closest('.sr-only, [hidden], dialog:not([open])'))
      .filter((e) => {
        const r = e.getBoundingClientRect()
        const cs = getComputedStyle(e)
        return r.width > 0 && cs.visibility !== 'hidden' && !(e as HTMLInputElement).disabled && !e.classList.contains('sr-only')
      })
      .flatMap((e) => {
        // checkboxes and radios are operated through their label, which is the larger target
        const lab = e instanceof HTMLInputElement ? (e.labels?.[0] ?? e) : e
        const r = (lab as HTMLElement).getBoundingClientRect()
        return r.height < 43.5 || r.width < 43.5 ? [`${e.tagName}.${e.className?.toString().slice(0, 24)} ${Math.round(r.width)}x${Math.round(r.height)} "${(e.textContent ?? '').trim().slice(0, 18)}"`] : []
      }),
  )

for (const lang of LANGS)
  for (const w of WIDTHS)
    test(`every route at ${w}px in ${lang}: no horizontal scroll, nothing wider than the screen, touch targets of 44 px`, async ({ page }) => {
      test.setTimeout(180_000)
      await page.setViewportSize({ width: w, height: 800 })
      await setLangInit(page, lang)
      await reviewReady(page, { imageKept: true })
      const problems: string[] = []
      for (const r of ROUTES) {
        await r.go(page)
        await page.locator(r.ready).first().waitFor({ timeout: 15_000 })
        // measure with the web fonts in place: while Noto Tamil/Devanagari is still loading the fallback font is wider and overflowed by a few px
        await page.evaluate(() => document.fonts.ready)
        await page.waitForTimeout(250)
        const ov = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
        if (ov > 0) problems.push(`${r.name}: page scrolls sideways by ${ov}px`)
        const ww = await wide(page)
        if (ww.length) problems.push(`${r.name}: wider than screen: ${ww.join(', ')}`)
        if (w >= 360) {
          const tt = await targets(page)
          if (tt.length) problems.push(`${r.name}: small targets: ${tt.slice(0, 4).join('; ')}`)
        }
      }
      expect(problems).toEqual([])
    })

test.describe('phone specifics', () => {
  test.use({ viewport: { width: 390, height: 800 }, hasTouch: true })

  test('how it works: a vertical pipeline replaces the diagram; every step and both outcomes are there, plus the negated safety sentence', async ({ page }) => {
    await page.goto('/how-it-works')
    await expect(page.locator('.pipeline-wrap')).toBeHidden()
    const v = page.locator('.pl-vertical')
    await expect(v).toBeVisible()
    for (const n of ['Your photo', 'Reading', 'Your check', 'Explanation', 'Interactions', 'Interaction found', 'Could not check']) await expect(v.getByText(n, { exact: true })).toBeVisible()
    await expect(v.getByText('Your step')).toHaveCount(2)
    await expect(page.getByText('This does not mean they are safe.')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(0)
  })

  test('how it works at 768 px shows the diagram, not the vertical version', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 800 })
    await page.goto('/how-it-works')
    await expect(page.locator('.pipeline-wrap')).toBeVisible()
    await expect(page.locator('.pl-vertical')).toBeHidden()
  })

  test('upload: the camera input is offered and the choose-file button is visible and tappable', async ({ page }) => {
    await reviewReady(page)
    await page.goto('/upload')
    await expect(page.locator('#file-camera')).toHaveAttribute('capture', 'environment')
    for (const name of ['Choose a file', 'Take a photo']) {
      const b = (await page.locator('label.btn', { hasText: name }).boundingBox())!
      expect(b.height).toBeGreaterThanOrEqual(44)
    }
  })

  test('schedule: slots are readable and the taken and skipped buttons are tappable', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/schedule`)
    await page.locator('.slot').first().waitFor()
    for (const b of await page.locator('.slot-actions .btn').all()) expect((await b.boundingBox())!.height).toBeGreaterThanOrEqual(44)
    await page.locator('.slot').first().locator('.slot-actions .btn').first().click()
    await expect(page.locator('.slot').first().locator('.slot-actions .btn').first()).toHaveAttribute('aria-pressed', 'true')
  })

  test('result: sections stack and the interaction cards stay readable', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/result`)
    await page.locator('.res-section').first().waitFor()
    const boxes = await page.locator('.res-section').evaluateAll((l) => l.map((e) => { const r = e.getBoundingClientRect(); return [r.left, r.right] }))
    for (const [l, r] of boxes) {
      expect(l).toBeGreaterThanOrEqual(0)
      expect(r).toBeLessThanOrEqual(390)
    }
    expect(await page.locator('.res-section').evaluateAll((l) => new Set(l.map((e) => Math.round(e.getBoundingClientRect().left))).size)).toBe(1) // one column
  })

  test('delete dialog fits the screen and its buttons are tappable', async ({ page }) => {
    await reviewReady(page)
    await page.goto('/documents')
    await page.locator('.menu-btn').click()
    await page.locator('.delete-btn').first().click()
    const dlg = page.getByRole('dialog')
    await expect(dlg).toBeVisible()
    const b = (await dlg.boundingBox())!
    expect(b.x).toBeGreaterThanOrEqual(0)
    expect(b.x + b.width).toBeLessThanOrEqual(390)
    for (const btn of await dlg.getByRole('button').all()) expect((await btn.boundingBox())!.height).toBeGreaterThanOrEqual(44)
  })

  test('reflow: 640 px (200 percent zoom of a desktop window) and 320 px (WCAG 1.4.10) show the landing and review pages without sideways scrolling', async ({ page }) => {
    await reviewReady(page)
    for (const w of [640, 320]) {
      await page.setViewportSize({ width: w, height: 800 })
      for (const path of ['/', `/d/${DOC_ID}/review`]) {
        await page.goto(path)
        await page.locator('h1').first().waitFor()
        await page.waitForTimeout(300)
        expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth), `${path} at ${w}`).toBeLessThanOrEqual(0)
      }
    }
  })
})

for (const lang of LANGS)
  test(`how it works (${lang}) at 1280 px: no label of the diagram is cut off by its box`, async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await setLangInit(page, lang)
    await page.goto('/how-it-works')
    if (lang === 'ta') {
      await expect(page.locator('.pipeline-wrap')).toBeHidden() // Tamil uses the vertical flow
      await expect(page.locator('.pl-vertical')).toBeVisible()
      return
    }
    const cut = await page.evaluate(() =>
      [...document.querySelectorAll('.pipeline g')].flatMap((g) => {
        const rect = g.querySelector('rect')!.getBBox()
        return [...g.querySelectorAll('text.pl-title')].flatMap((t) => (t.getBBox().x + t.getBBox().width > rect.x + rect.width - 4 ? [t.textContent] : []))
      }).concat(
        [...document.querySelectorAll('.pipeline > text.pl-title')].flatMap((t) => {
          const r = t.previousElementSibling?.previousElementSibling as SVGGraphicsElement | null // the rect before the icon
          return r && t.getBBox().width > r.getBBox().width - 8 ? [t.textContent] : []
        }),
      ),
    )
    expect(cut).toEqual([])
  })
