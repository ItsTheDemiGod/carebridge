import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { setLangInit } from './flowhelpers'
import { mockApi } from './mock'

/* Phase 6d: "Delete my data" is reachable in at most two interactions at every width, in every language, without overflow or a wrapped header.
 * 768 px and wider with a collapsed header: an icon button beside Menu (one interaction); below: Menu, then the text button (two). */
const WIDTHS = [320, 360, 390, 768, 1024, 1280, 1440, 1920]
for (const lang of ['en', 'ta', 'hi'] as const)
  for (const w of WIDTHS)
    test(`delete is reachable in at most two interactions at ${w}px in ${lang}; no overflow, header not wrapped`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: 800 })
      await setLangInit(page, lang)
      await mockApi(page, { consented: true })
      await page.goto('/documents')
      await page.locator('h1').first().waitFor()
      await page.evaluate(() => document.fonts.ready)
      expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth), 'horizontal overflow').toBeLessThanOrEqual(0)
      const hdr = await page.locator('.site-header .header-row').evaluate((row) => {
        const r = row.getBoundingClientRect()
        const kids = [...row.children].filter((c) => getComputedStyle(c).display !== 'none' && c.getBoundingClientRect().width > 0) as HTMLElement[]
        return { height: r.height, right: Math.max(...kids.map((k) => k.getBoundingClientRect().right)), spread: Math.max(...kids.map((k) => k.getBoundingClientRect().top)) - Math.min(...kids.map((k) => k.getBoundingClientRect().top)) }
      })
      expect(hdr.height, 'header row not wrapped').toBeLessThan(90)
      expect(hdr.right, 'inside the viewport').toBeLessThanOrEqual(w)
      // count the interactions a person needs
      let steps = 0
      const icon = page.locator('.delete-icon')
      const rowButton = page.locator('.header-menu .delete-btn')
      if (await icon.isVisible()) {
        const b = (await icon.boundingBox())!
        expect(b.width).toBeGreaterThanOrEqual(44)
        expect(b.height).toBeGreaterThanOrEqual(44)
        await icon.focus()
        await expect(icon).toHaveAttribute('aria-label', /.+/)
        expect(await icon.evaluate((e) => getComputedStyle(e, '::after').opacity), 'tooltip on focus').toBe('1')
        await icon.click()
        steps = 1
      } else {
        if (!(await rowButton.isVisible())) {
          await page.locator('.menu-btn').click()
          steps++
        }
        await rowButton.click()
        steps++
      }
      expect(steps).toBeLessThanOrEqual(2)
      await expect(page.getByRole('dialog')).toBeVisible()
      if (w < 768) await expect(icon, 'no icon button on phones (Menu must stay on screen)').toBeHidden()
    })

for (const lang of ['en', 'ta', 'hi'] as const)
  for (const w of [390, 1024]) // 1024: the collapsed header with the icon button
    test(`axe: header in ${lang} at ${w}px`, async ({ browser }) => {
      const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: w, height: 800 } })
      await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
      const page = await ctx.newPage()
      await mockApi(page, { consented: true })
      await page.goto('/documents')
      await page.locator('h1').first().waitFor()
      await page.evaluate(() => document.fonts.ready)
      const r = await new AxeBuilder({ page }).include('.site-header').withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
      expect(r.violations.map((v) => `${v.impact} ${v.id}: ${v.nodes[0].target.join(' ')}`)).toEqual([])
      await ctx.close()
    })
