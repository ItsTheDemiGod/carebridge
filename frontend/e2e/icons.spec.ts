import { expect, test } from '@playwright/test'
import { DOC_ID } from './flowhelpers'
import { setLangInit } from './flowhelpers'
import { mockApi } from './mock'

const ROUTES = ['/', '/how-it-works', '/privacy', '/start', '/consent', '/upload', '/documents', `/d/${DOC_ID}/review`, `/d/${DOC_ID}/result`, `/d/${DOC_ID}/schedule`, `/d/${DOC_ID}/summary`, '/no-such-page']

for (const lang of ['en', 'ta'])
  test(`no icon is empty or zero-sized on the main routes (${lang})`, async ({ page }) => {
    test.setTimeout(120_000)
    await setLangInit(page, lang)
    await mockApi(page, { consented: true, docReady: true })
    for (const r of ROUTES) {
      await page.goto(r)
      await page.locator('h1').first().waitFor()
      await page.waitForTimeout(300)
      const bad = await page.evaluate(() =>
        [...document.querySelectorAll('svg[viewBox="0 0 24 24"]')].flatMap((s) => {
          const b = s.getBoundingClientRect()
          const hidden = !s.getClientRects().length // display:none (e.g. the closed menu) is not on screen
          return !hidden && (b.width < 8 || b.height < 8 || !s.querySelector('path,circle,rect')) ? [`${Math.round(b.width)}x${Math.round(b.height)} ${(s.parentElement?.className ?? '').toString().slice(0, 30)}`] : []
        }),
      )
      expect(bad, r).toEqual([])
      const unnamed = await page.evaluate(() => [...document.querySelectorAll('svg[viewBox="0 0 24 24"]')].filter((s) => s.getAttribute('role') === 'img' && !s.getAttribute('aria-label')).length)
      expect(unnamed, `meaningful icons need a name on ${r}`).toBe(0)
    }
  })
