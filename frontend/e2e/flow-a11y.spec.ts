import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { DOC_ID, PNG, card, openCard, pressDelete, reviewReady } from './flowhelpers'
import { mockApi } from './mock'

/* axe (WCAG 2.0/2.1/2.2 A and AA) on every flow route at its key states, in en, ta and hi, against the mocked API. */
type State = { name: string; run: (p: Page) => Promise<void> }
const settle = (p: Page) => p.waitForTimeout(400)
const STATES: State[] = [
  { name: 'consent', run: async (p) => { await mockApi(p, { hasSession: true }); await p.goto('/consent'); await p.locator('.purposes').waitFor() } },
  { name: 'upload', run: async (p) => { await mockApi(p, { consented: true }); await p.goto('/upload'); await p.locator('.dropzone').waitFor() } },
  { name: 'upload-preview', run: async (p) => { await mockApi(p, { consented: true }); await p.goto('/upload'); await p.locator('#file-pick').setInputFiles({ name: 'a.png', mimeType: 'image/png', buffer: PNG }); await p.locator('.preview img').waitFor() } },
  { name: 'processing', run: async (p) => { await mockApi(p, { consented: true, docSteps: ['extracting'] }); await p.goto('/upload'); await p.locator('#file-pick').setInputFiles({ name: 'a.png', mimeType: 'image/png', buffer: PNG }); await p.locator('.preview img').waitFor(); await p.locator('.preview .btn-primary').click(); await p.getByRole('progressbar').waitFor() } },
  { name: 'processing-failed', run: async (p) => { await mockApi(p, { consented: true, docSteps: ['failed'], errorCode: 'timeout' }); await p.goto('/upload'); await p.locator('#file-pick').setInputFiles({ name: 'a.png', mimeType: 'image/png', buffer: PNG }); await p.locator('.preview .btn-primary').click(); await p.locator('.notice').waitFor() } },
  { name: 'review', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/review`); await card(p, 1).waitFor() } },
  { name: 'review-open', run: async (p) => {
      await reviewReady(p); await p.goto(`/d/${DOC_ID}/review`); await card(p, 1).waitFor()
      await card(p, 1).locator('input[type=radio]').nth(1).check()
      await card(p, 1).getByRole('combobox').first().fill('p'); await p.getByRole('listbox').first().waitFor()
      await card(p, 2).locator('input[type=radio]').nth(0).check()
      await p.locator('main .add-med, main button:has(svg)').first().waitFor() } },
  { name: 'review-saved', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/review`); await card(p, 3).waitFor(); const c3 = await openCard(p, 3); await c3.locator('input[type=radio]').nth(3).check(); await c3.locator('.card-confirm .btn').click(); await p.locator('.summary-bar .btn').click(); await p.locator('.saved-panel').waitFor() } },
  { name: 'result', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/result`); await p.locator('.res-section').first().waitFor() } },
  { name: 'schedule', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/schedule`); await p.locator('.slot').first().waitFor() } },
  { name: 'summary', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/summary`); await p.locator('.summary-table').waitFor() } },
  { name: 'documents', run: async (p) => { await reviewReady(p); await p.goto('/documents'); await p.locator('.res-lines').waitFor() } },
  { name: 'delete-dialog', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/result`); await p.locator('.res-section').first().waitFor(); await pressDelete(p); await p.getByRole('dialog').waitFor() } },
  { name: 'leave-dialog', run: async (p) => { await reviewReady(p); await p.goto(`/d/${DOC_ID}/review`); await card(p, 1).waitFor(); await card(p, 1).locator('input[type=radio]').nth(3).check(); await card(p, 1).locator('.card-confirm .btn').click(); await p.locator('.page-actions a').last().click(); await p.getByRole('dialog').waitFor() } },
]

for (const lang of ['en', 'ta', 'hi'] as const)
  for (const st of STATES)
    test(`axe flow: ${st.name} in ${lang}`, async ({ browser }) => {
      const c = await browser.newContext({ reducedMotion: 'reduce' })
      await c.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
      const p = await c.newPage()
      await st.run(p)
      await settle(p)
      const r = await new AxeBuilder({ page: p }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
      const lines = r.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}: ${v.nodes[0].target.join(' ')}`)
      if (lines.length) console.log(`[axe ${lang} ${st.name}]\n  ${lines.join('\n  ')}`)
      expect(r.violations.map((v) => `${v.impact} ${v.id}`)).toEqual([])
      await c.close()
    })
