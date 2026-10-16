import { expect, test, type Page } from '@playwright/test'
import { LANGS, ROUTES, blockApi, setLang, watch } from './helpers'

for (const lang of LANGS) {
  test(`landing renders in ${lang} without console errors, with the right lang attribute and fonts`, async ({ page, context }) => {
    await setLang(context, lang)
    const errors = watch(page)
    await blockApi(page) // the landing page must not need the backend
    await page.goto('/', { waitUntil: 'networkidle' })
    await expect(page.locator('h1')).toBeVisible()
    await expect(page.locator('html')).toHaveAttribute('lang', lang)
    const loaded = await page.evaluate(async () => {
      await document.fonts.ready
      return [...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family.replace(/"/g, ''))
    })
    const expected = { en: ['Fraunces Variable', 'Noto Sans'], ta: ['Noto Sans Tamil', 'Noto Serif Tamil'], hi: ['Noto Sans Devanagari', 'Noto Serif Devanagari'] }[lang]
    for (const f of expected) expect(loaded, `font ${f}`).toContain(f)
    const used = await page.evaluate(() => getComputedStyle(document.querySelector('h1')!).fontFamily)
    if (lang !== 'en') expect(used).toContain(lang === 'ta' ? 'Noto Serif Tamil' : 'Noto Serif Devanagari')
    expect(errors).toEqual([])
  })
}

test('Tamil and Devanagari sample text is covered by the loaded Noto faces (no tofu)', async ({ browser }) => {
  for (const [lang, sample, family] of [['ta', 'தமிழ்', 'Noto Sans Tamil'], ['hi', 'हिन्दी', 'Noto Sans Devanagari']] as const) {
    const c = await browser.newContext()
    await setLang(c, lang)
    const p = await c.newPage()
    await p.goto('/', { waitUntil: 'networkidle' })
    const ok = await p.evaluate(
      async ([s, f]) => {
        await document.fonts.ready
        return document.fonts.check(`16px "${f}"`, s)
      },
      [sample, family],
    )
    expect(ok, lang).toBe(true)
    await c.close()
  }
})

for (const w of [360, 768, 1280, 1920]) {
  test(`no horizontal overflow at ${w}px on every route in every language`, async ({ browser }) => {
    for (const lang of LANGS) {
      const c = await browser.newContext({ viewport: { width: w, height: 900 } })
      await setLang(c, lang)
      const p = await c.newPage()
      for (const r of ROUTES) {
        await p.goto(r, { waitUntil: 'networkidle' })
        const o = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }))
        expect(o.sw, `${lang} ${r}`).toBeLessThanOrEqual(o.cw)
      }
      await c.close()
    }
  })
}

test('skip link is first in tab order and moves focus to main', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' })
  await page.keyboard.press('Tab')
  await expect(page.locator('.skip-link')).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('main')).toBeFocused()
})

test('tab order reaches the header controls with a visible focus ring', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' })
  const seen: string[] = []
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press('Tab')
    const f = await page.evaluate(() => {
      const e = document.activeElement as HTMLElement
      const s = getComputedStyle(e)
      return { tag: e.tagName, text: (e.textContent ?? '').trim().slice(0, 20), outline: parseFloat(s.outlineWidth), style: s.outlineStyle }
    })
    expect(f.outline, `${f.tag} ${f.text}`).toBeGreaterThanOrEqual(2)
    expect(f.style).not.toBe('none')
    seen.push(f.text)
  }
  expect(seen.some((t) => /English/.test(t)) && seen.some((t) => /Calm/.test(t))).toBe(true)
})

test('ambient layer runs by default (canvas animating, cursor ring present, tiles drifting)', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' })
  const c = page.locator('canvas.ambient-canvas')
  await expect(c).toHaveAttribute('data-running', 'true')
  await page.mouse.move(300, 300)
  await page.mouse.move(500, 420)
  await expect(page.locator('.cursor-ring')).toHaveCount(1)
  await page.waitForTimeout(800)
  expect(Number((await c.getAttribute('data-frames')) ?? 0)).toBeGreaterThan(5)
  expect(await page.evaluate(() => getComputedStyle(document.querySelector('.mosaic-cell')!).animationName)).toBe('drift')
})

async function expectMotionOff(page: Page) {
  const canvas = page.locator('canvas.ambient-canvas')
  await expect(canvas).toHaveAttribute('data-running', 'false')
  await expect(page.locator('.cursor-ring')).toHaveCount(0)
  expect(await page.evaluate(() => getComputedStyle(document.querySelector('.mosaic-cell')!).animationName)).toBe('none')
  const frames = await canvas.getAttribute('data-frames')
  await page.waitForTimeout(500)
  expect(await canvas.getAttribute('data-frames')).toBe(frames)
  await expect(page.locator('.reveal')).toHaveCount(0)
}

test('prefers-reduced-motion turns the ambient layer, cursor ring and tile drift off', async ({ browser }) => {
  const c = await browser.newContext({ reducedMotion: 'reduce' })
  const p = await c.newPage()
  await p.goto('/', { waitUntil: 'networkidle' })
  await p.mouse.move(200, 200)
  await expectMotionOff(p)
  await c.close()
})

test('calm mode turns the same things off, persists after reload, and stores only its two preferences', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' })
  const toggle = page.getByRole('button', { name: /Calm mode/ })
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-pressed', 'true')
  await page.mouse.move(250, 250)
  await expectMotionOff(page)
  await page.reload({ waitUntil: 'networkidle' })
  await expect(page.getByRole('button', { name: /Calm mode/ })).toHaveAttribute('aria-pressed', 'true')
  await expectMotionOff(page)
  const keys = await page.evaluate(() => Object.keys(localStorage).sort())
  expect(keys.every((k) => ['carebridge.calm', 'carebridge.language'].includes(k))).toBe(true)
  expect(await page.evaluate(() => document.cookie)).toBe('')
})

test('works offline after the first load and makes no cross-origin requests', async ({ page, context }) => {
  const external: string[] = []
  page.on('request', (r) => {
    const u = new URL(r.url())
    if (u.protocol.startsWith('http') && !['localhost', '127.0.0.1'].includes(u.hostname)) external.push(r.url())
  })
  await page.goto('/', { waitUntil: 'networkidle' })
  await context.setOffline(true)
  await page.getByRole('link', { name: 'How it works' }).first().click()
  await expect(page.locator('h1')).toContainText('How CareBridge works')
  await page.getByRole('button', { name: 'தமிழ்' }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', 'ta')
  await page.getByRole('link', { name: 'தனியுரிமை' }).first().click()
  await expect(page.locator('.notice-slot .notice')).toBeVisible() // the backend-unreachable message, no crash
  expect(external).toEqual([])
})

for (const lang of ['ta', 'hi'] as const) {
  test(`the draft-translation note is visible on every route in ${lang}`, async ({ browser }) => {
    const c = await browser.newContext()
    await setLang(c, lang)
    const p = await c.newPage()
    const text = lang === 'ta' ? 'இயந்திரம் வரைந்த மொழிபெயர்ப்பு' : 'मशीन से तैयार किया गया अनुवाद'
    for (const r of ROUTES) {
      await p.goto(r, { waitUntil: 'networkidle' })
      await expect(p.locator('.draft-note'), r).toContainText(text)
    }
    await c.close()
  })
}

test('no draft note in English', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' })
  await expect(page.locator('.draft-note')).toHaveCount(0)
})

test('privacy page shows the live notice when the backend is up', async ({ page }) => {
  await page.goto('/privacy', { waitUntil: 'networkidle' })
  await expect(page.getByText(/Notice version/)).toBeVisible({ timeout: 10_000 })
  await expect(page.locator('.consent-list li').first()).toBeVisible()
})

test('privacy page shows a clear message when the backend is unreachable, and recovers on retry', async ({ page }) => {
  await blockApi(page)
  await page.goto('/privacy', { waitUntil: 'networkidle' })
  await expect(page.getByText('is not reachable')).toBeVisible()
  await page.unroute('**/api/**')
  await page.getByRole('button', { name: 'Try again' }).click()
  await expect(page.getByText(/Notice version/)).toBeVisible({ timeout: 10_000 })
})

test('404 route and the /start placeholder', async ({ page }) => {
  await page.goto('/nope/at/all', { waitUntil: 'networkidle' })
  await expect(page.locator('h1')).toHaveText('Page not found')
  expect(await page.title()).toContain('Page not found')
  await page.goto('/start', { waitUntil: 'networkidle' })
  await expect(page.locator('h1')).toContainText('working flow')
})

test('document title follows the route and the language', async ({ page }) => {
  await page.goto('/how-it-works', { waitUntil: 'networkidle' })
  expect(await page.title()).toContain('How it works')
  await page.getByRole('button', { name: 'हिन्दी' }).click()
  await expect(page).toHaveTitle(/यह कैसे काम करता है/)
})
