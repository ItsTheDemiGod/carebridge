import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { setLangInit } from './flowhelpers'
import { mockApi } from './mock'

const LANGS = ['en', 'ta', 'hi'] as const
const WIDTHS = [360, 390, 768, 1024, 1280, 1440, 1920]

for (const lang of LANGS)
  for (const w of WIDTHS)
    for (const session of [false, true])
      test(`header at ${w}px in ${lang}${session ? ' with a session (delete control)' : ''}: one row on desktop, menu on small, no overflow`, async ({ page }) => {
        await page.setViewportSize({ width: w, height: 800 })
        await setLangInit(page, lang)
        await mockApi(page, { consented: session })
        await page.goto(session ? '/documents' : '/how-it-works')
        await page.locator('h1').first().waitFor()
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
        expect(overflow, 'horizontal overflow').toBeLessThanOrEqual(0)
        const desktop = lang === 'ta' ? w >= 1280 : w >= 1024 // Tamil labels are twice as wide: it keeps the menu below 80 rem
        const menuBtn = page.locator('.menu-btn')
        if (desktop) {
          await expect(menuBtn).toBeHidden()
          const m = await page.evaluate(() => {
            const items = [...document.querySelectorAll('.site-header .brand-link, .site-header .site-nav a, .site-header .nav-start, .site-header .header-tools button')] as HTMLElement[]
            const tops = items.map((e) => { const r = e.getBoundingClientRect(); return r.top + r.height / 2 })
            const clipped = items.filter((e) => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible').length
            const right = Math.max(...items.map((e) => e.getBoundingClientRect().right))
            const lines = items.filter((e) => e.getBoundingClientRect().height > 60).length
            return { spread: Math.max(...tops) - Math.min(...tops), height: document.querySelector('.site-header')!.getBoundingClientRect().height, clipped, right, lines, n: items.length }
          })
          expect(m.spread, `controls on one row (${JSON.stringify(m)})`).toBeLessThan(8)
          expect(m.height, 'header height').toBeLessThan(90)
          expect(m.right, 'inside viewport').toBeLessThanOrEqual(w)
          expect(m.lines, 'no wrapped text').toBe(0)
        } else {
          await expect(menuBtn).toBeVisible()
          await expect(page.locator('#site-menu')).toBeHidden()
          expect(await page.locator('.site-header').evaluate((e) => e.getBoundingClientRect().height)).toBeLessThan(90)
          await menuBtn.click()
          await expect(menuBtn).toHaveAttribute('aria-expanded', 'true')
          await expect(page.locator('#site-menu')).toBeVisible()
          const box = await page.locator('#site-menu').evaluate((e) => { const r = e.getBoundingClientRect(); return { r: r.right, sw: e.scrollWidth - e.clientWidth } })
          expect(box.r).toBeLessThanOrEqual(w)
          expect(box.sw).toBeLessThanOrEqual(0)
          for (const el of await page.locator('#site-menu a, #site-menu button').all()) expect((await el.boundingBox())!.height, 'touch target').toBeGreaterThanOrEqual(43)
          await page.keyboard.press('Escape')
          await expect(menuBtn).toHaveAttribute('aria-expanded', 'false')
          await expect(menuBtn).toBeFocused()
        }
      })

test('menu: opens by keyboard, reaches every control, closes on Escape (focus returns) and on route change', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 })
  await mockApi(page)
  await page.goto('/')
  const btn = page.locator('.menu-btn')
  await btn.focus()
  await page.keyboard.press('Enter')
  await expect(btn).toHaveAttribute('aria-expanded', 'true')
  const names: string[] = []
  for (let i = 0; i < 9; i++) {
    await page.keyboard.press('Tab')
    names.push(await page.evaluate(() => ((document.activeElement as HTMLElement).textContent ?? '').trim()))
  }
  for (const n of ['How it works', 'Privacy', 'Limits', 'Your documents', 'Start', 'English', 'Calm mode']) expect(names.join('|')).toContain(n)
  await page.keyboard.press('Escape')
  await expect(btn).toBeFocused()
  await btn.click()
  await page.getByRole('link', { name: 'Privacy' }).first().click()
  await page.waitForURL('**/privacy')
  await expect(btn).toHaveAttribute('aria-expanded', 'false')
  await expect(page.locator('#site-menu')).toBeHidden()
})

test('menu is a plain disclosure: the language and calm controls inside it work', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 })
  await mockApi(page)
  await page.goto('/')
  await page.locator('.menu-btn').click()
  await page.getByRole('button', { name: 'हिन्दी' }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', 'hi')
  await expect(page.locator('.menu-btn')).toHaveAttribute('aria-expanded', 'true') // stays open while changing settings
})

for (const lang of LANGS)
  for (const w of [390, 1280])
    test(`axe: header with the menu open in ${lang} at ${w}px`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: 800 })
      await setLangInit(page, lang)
      await mockApi(page, { consented: true })
      await page.goto('/documents')
      if (await page.locator('.menu-btn').isVisible()) await page.locator('.menu-btn').click()
      const r = await new AxeBuilder({ page }).include('.site-header').withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
      expect(r.violations.map((v) => `${v.id} ${v.nodes.length}`)).toEqual([])
    })
