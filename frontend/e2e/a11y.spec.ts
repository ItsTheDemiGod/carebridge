import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { ROUTES, setLang } from './helpers'

for (const lang of ['en', 'ta'] as const)
  for (const route of ROUTES) {
    test(`axe: ${route} in ${lang}`, async ({ browser }) => {
      const c = await browser.newContext({ reducedMotion: 'reduce' }) // stable layout, reveals are plain
      await setLang(c, lang)
      const p = await c.newPage()
      await p.goto(route, { waitUntil: 'networkidle' })
      if (route === '/privacy') await p.locator('.consent-list').waitFor({ timeout: 10_000 })
      const r = await new AxeBuilder({ page: p }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
      const lines = r.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}: ${v.nodes[0].target.join(' ')}`)
      if (lines.length) console.log(`[axe ${lang} ${route}]\n  ${lines.join('\n  ')}`)
      expect(r.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical').map((v) => v.id)).toEqual([])
      await c.close()
    })
  }
