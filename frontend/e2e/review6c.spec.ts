import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { DOC_ID, card, openCard, reviewReady, setLangInit } from './flowhelpers'

const headings = (page: Page) => page.locator('article.med-card h3.med-name').allInnerTexts()
const transform = (page: Page, scope: string) => page.locator(`${scope} .pv-frame img`).evaluate((i) => (i as HTMLElement).style.transform)
const nums = (t: string) => (t.match(/-?[\d.]+(?=px|\))/g) ?? []).map(Number) // [x, y, zoom]

test.describe('review page: list', () => {
  test('needs-attention medicines come first with their position in the document; the toggle restores document order', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await page.locator('article.med-card').first().waitFor()
    expect(await headings(page)).toEqual(['Netfornin', 'Alendronate', 'Pantop', 'Glycomet'])
    expect(await page.locator('.rv-num span[aria-hidden]').allInnerTexts()).toEqual(['#2', '#3', '#4', '#1'])
    await expect(page.locator('.rv-num .sr-only').first()).toHaveText('Medicine 2 on your document')
    await page.getByRole('button', { name: 'Show in document order' }).click()
    expect(await headings(page)).toEqual(['Glycomet', 'Netfornin', 'Alendronate', 'Pantop'])
    await page.getByRole('button', { name: 'Show needs-attention first' }).click()
    expect(await headings(page)).toEqual(['Netfornin', 'Alendronate', 'Pantop', 'Glycomet'])
  })

  test('a card does not move when it is checked (order follows the API level, not the decisions)', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await card(page, 1).getByLabel('Remove: this is not on my document').check()
    await card(page, 1).getByRole('button', { name: 'Remove this medicine' }).click()
    expect(await headings(page)).toEqual(['Netfornin', 'Alendronate', 'Pantop', 'Glycomet'])
  })

  test('status chips use the API level and the saved decisions; cards that need nothing start folded, attention cards cannot be folded', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await expect(card(page, 1).locator('.rv-chip')).toHaveText('Needs your check')
    await expect(card(page, 0).locator('.rv-chip')).toHaveText('No action needed')
    await expect(card(page, 3).locator('.rv-chip')).toHaveText('No action needed')
    await expect(card(page, 3).locator('.review-badge')).toHaveText('Note') // the note is not hidden by folding
    // attention: open, no fold button
    await expect(page.locator('#rv-body-1')).toBeVisible()
    await expect(page.locator('#rv-toggle-1')).toHaveCount(0)
    // folded: body hidden, name, strength, chip and Edit remain
    await expect(page.locator('#rv-body-0')).toBeHidden()
    const c0 = card(page, 0)
    await expect(c0.getByRole('heading', { level: 3, name: 'Glycomet' })).toBeVisible()
    await expect(c0.getByText('500 mg').first()).toBeVisible()
    const edit = page.locator('#rv-toggle-0')
    await expect(edit).toHaveText('Edit')
    await expect(edit).toHaveAttribute('aria-expanded', 'false')
    await edit.click()
    await expect(edit).toHaveAttribute('aria-expanded', 'true')
    await expect(edit).toHaveText('Collapse')
    await expect(page.locator('#rv-body-0')).toBeVisible()
    // folding keeps the decision
    await c0.getByLabel('This matches my document').check()
    await c0.getByRole('button', { name: 'Collapse' }).click()
    await expect(page.locator('#rv-body-0')).toBeHidden()
    await c0.getByRole('button', { name: 'Edit' }).click()
    await expect(c0.getByLabel('This matches my document')).toBeChecked()
  })

  test('a checked card folds with the chip "Checked by you" and reopens for editing without losing the decision (heading structure stays h2 > h3)', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    const c = card(page, 1)
    await c.getByLabel('Remove: this is not on my document').check()
    await c.getByRole('button', { name: 'Remove this medicine' }).click()
    await expect(c.locator('.rv-chip')).toHaveText('Checked by you')
    await expect(page.locator('#rv-body-1')).toBeHidden()
    await c.getByRole('button', { name: 'Edit' }).click()
    await expect(c.getByLabel('Remove: this is not on my document')).toBeChecked()
    expect(await page.locator('main h2').allInnerTexts()).toContain('Medicines found on your document')
    expect(await page.locator('article.med-card h3').count()).toBeGreaterThanOrEqual(4)
  })

  test('progress counts are in a polite live region, update with each check, and "jump" walks the cards that still need a check', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    const live = page.locator('.rv-counts')
    await expect(live).toHaveAttribute('aria-live', 'polite')
    await expect(live).toContainText('0 of 4 medicines checked')
    await expect(live).toContainText('2 still need your check')
    const jump = page.getByRole('button', { name: 'Jump to the next one that needs your check' })
    await jump.click()
    await expect(page.locator('#rv-h-1')).toBeFocused()
    await jump.click()
    await expect(page.locator('#rv-h-2')).toBeFocused()
    await card(page, 1).getByLabel('Remove: this is not on my document').check()
    await card(page, 1).getByRole('button', { name: 'Remove this medicine' }).click()
    await expect(live).toContainText('1 of 4 medicines checked')
    await expect(live).toContainText('1 still need your check')
    await card(page, 2).getByLabel('Remove: this is not on my document').check()
    await card(page, 2).getByRole('button', { name: 'Remove this medicine' }).click()
    await expect(live).toContainText('2 of 4 medicines checked')
    await expect(live).toContainText('Every medicine that must be confirmed has your check.')
    await expect(jump).toBeDisabled()
  })

  test('the one-line reading: no repeated abbreviation, number and label', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await openCard(page, 0)
    const line = await card(page, 0).locator('.rv-read .rv-line').innerText()
    expect(line).toBe('500 mg · 1 tablet · twice a day, after meals · 5 days')
    expect(await card(page, 0).locator('dl.facts').count()).toBe(0)
  })
})

test.describe('review page: photo pane (desktop)', () => {
  test.use({ viewport: { width: 1280, height: 800 } })

  test('two panes: the photo pane is sticky and fills the viewport below the header and bar; the page notes that the paper is the reference', async ({ page }) => {
    await reviewReady(page, { imageKept: true })
    await page.goto(`/d/${DOC_ID}/review`)
    await expect(page.locator('.rv-pane .pv-frame img')).toBeVisible()
    await page.evaluate(() => window.scrollTo(0, 600))
    await page.waitForTimeout(300)
    const box = await page.locator('.rv-pane').boundingBox()
    const bar = await page.locator('.rv-bar').boundingBox()
    expect(box!.y).toBeGreaterThan(bar!.y + bar!.height - 2) // below the bar
    expect(box!.y + box!.height).toBeLessThanOrEqual(800)
    expect(box!.height).toBeGreaterThan(400)
    await expect(page.locator('.rv-pane').getByText('Your paper document is the reference')).toBeVisible()
    await expect(page.locator('.phone-photo')).toBeHidden()
  })

  test('zoom in, zoom out and reset buttons (icon + accessible name); keyboard: plus, minus, arrows and 0', async ({ page }) => {
    await reviewReady(page, { imageKept: true })
    await page.goto(`/d/${DOC_ID}/review`)
    await expect(page.locator('.rv-pane .pv-frame img')).toBeVisible()
    const pane = page.locator('.rv-pane')
    const zin = pane.getByRole('button', { name: 'Zoom in' })
    const zout = pane.getByRole('button', { name: 'Zoom out' })
    await expect(zout).toBeDisabled()
    await zin.click()
    expect(nums(await transform(page, '.rv-pane')).at(-1)).toBe(1.5)
    await pane.getByRole('button', { name: 'Reset view' }).click()
    expect(nums(await transform(page, '.rv-pane')).at(-1)).toBe(1)
    await pane.locator('.pv-frame').focus()
    for (let i = 0; i < 4; i++) await page.keyboard.press('+')
    expect(nums(await transform(page, '.rv-pane')).at(-1)).toBe(3)
    const before = nums(await transform(page, '.rv-pane'))
    await page.keyboard.press('ArrowLeft')
    const after = nums(await transform(page, '.rv-pane'))
    expect(after[0]).toBeGreaterThan(before[0]) // the picture moved right (we looked left)
    await page.keyboard.press('ArrowDown')
    expect(nums(await transform(page, '.rv-pane'))[1]).toBeLessThan(after[1])
    await page.keyboard.press('-')
    expect(nums(await transform(page, '.rv-pane')).at(-1)).toBe(2.5)
    await page.keyboard.press('0')
    expect(nums(await transform(page, '.rv-pane')).at(-1)).toBe(1)
  })

  test('drag pans a zoomed photo', async ({ page }) => {
    await reviewReady(page, { imageKept: true })
    await page.goto(`/d/${DOC_ID}/review`)
    const pane = page.locator('.rv-pane')
    await expect(pane.locator('.pv-frame img')).toBeVisible()
    for (let i = 0; i < 4; i++) await pane.getByRole('button', { name: 'Zoom in' }).click()
    await page.evaluate(() => window.scrollTo(0, 600))
    await page.waitForTimeout(900)
    const b = (await pane.locator('.pv-frame').boundingBox())!
    const t0 = nums(await transform(page, '.rv-pane'))
    await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2)
    await page.mouse.down()
    await page.mouse.move(b.x + b.width / 2 + 80, b.y + b.height / 2 + 60, { steps: 4 })
    await page.mouse.up()
    const t1 = nums(await transform(page, '.rv-pane'))
    expect(t1[0]).toBeGreaterThan(t0[0])
    expect(t1[1]).toBeGreaterThan(t0[1])
  })

  test('without a photo the plain message from 6b is shown', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await expect(page.locator('.rv-pane').getByText('hold your paper document next to the screen')).toBeVisible()
  })
})

test.describe('review page: phone (390 px)', () => {
  test.use({ viewport: { width: 390, height: 800 }, hasTouch: true })

  test('single column: no pane, a thumbnail and a Show photo button open a full-screen viewer dialog (focus trapped, Escape closes, focus returns)', async ({ page }) => {
    await reviewReady(page, { imageKept: true })
    await page.goto(`/d/${DOC_ID}/review`)
    await page.locator('article.med-card').first().waitFor()
    await expect(page.locator('.rv-pane')).toBeHidden()
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0)
    const show = page.locator('.phone-photo').getByRole('button', { name: 'Show my photo' }).last()
    await show.click()
    const dlg = page.getByRole('dialog', { name: 'Your photo' })
    await expect(dlg).toBeVisible()
    const vb = await dlg.boundingBox()
    expect(vb!.width).toBeGreaterThanOrEqual(388)
    expect(vb!.height).toBeGreaterThanOrEqual(790)
    await expect(dlg.getByRole('button', { name: 'Close the photo' })).toBeFocused()
    // focus stays inside the dialog
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab')
      expect(await page.evaluate(() => !document.activeElement || document.activeElement === document.body || !!document.activeElement.closest('dialog'))).toBe(true) // never on the page behind (it is inert)
    }
    await dlg.getByRole('button', { name: 'Zoom in' }).click()
    expect(nums(await transform(page, 'dialog')).at(-1)).toBe(1.5)
    await page.keyboard.press('Escape')
    await expect(dlg).toBeHidden()
    await expect(show).toBeFocused()
    // the thumbnail opens the same viewer; the close button closes it
    await page.locator('.rv-thumb').click()
    await expect(dlg).toBeVisible()
    await dlg.getByRole('button', { name: 'Close the photo' }).click()
    await expect(dlg).toBeHidden()
  })

  test('the viewer supports a two-finger pinch', async ({ page }) => {
    await reviewReady(page, { imageKept: true })
    await page.goto(`/d/${DOC_ID}/review`)
    await page.locator('.phone-photo').getByRole('button', { name: 'Show my photo' }).last().click()
    const frame = page.locator('dialog .pv-frame')
    await expect(frame.locator('img')).toBeVisible()
    const b = (await frame.boundingBox())!
    const cx = b.x + b.width / 2
    const cy = b.y + b.height / 2
    // synthesised pointer events: two touches moving apart
    await frame.evaluate(
      (el, p) => {
        const fire = (type: string, id: number, x: number, y: number) => el.dispatchEvent(new PointerEvent(type, { pointerId: id, pointerType: 'touch', clientX: x, clientY: y, bubbles: true, isPrimary: id === 1 }))
        fire('pointerdown', 1, p.cx - 40, p.cy)
        fire('pointerdown', 2, p.cx + 40, p.cy)
        fire('pointermove', 1, p.cx - 100, p.cy)
        fire('pointermove', 2, p.cx + 100, p.cy)
      },
      { cx, cy },
    )
    expect(nums(await transform(page, 'dialog')).at(-1)).toBeGreaterThan(1.5)
  })

  test('the progress bar sticks to the bottom and does not cover the last control; touch targets are at least 44 px', async ({ page }) => {
    await reviewReady(page, { imageKept: true })
    await page.goto(`/d/${DOC_ID}/review`)
    await page.locator('article.med-card').first().waitFor()
    const bar = (await page.locator('.rv-bar').boundingBox())!
    expect(bar.y + bar.height).toBeGreaterThanOrEqual(799)
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.waitForTimeout(300)
    const last = (await page.getByRole('link', { name: 'See results' }).boundingBox())!
    const bar2 = (await page.locator('.rv-bar').boundingBox())!
    expect(last.y + last.height).toBeLessThanOrEqual(bar2.y + 1)
    for (const loc of [page.locator('.jump-btn'), page.getByRole('button', { name: 'Save my checks' }), page.locator('.order-btn'), page.locator('#rv-toggle-0'), page.locator('.rv-thumb')]) {
      const bb = (await loc.boundingBox())!
      expect(bb.height, 'height').toBeGreaterThanOrEqual(43.5)
      expect(bb.width, 'width').toBeGreaterThanOrEqual(43.5)
    }
  })

  test('a focused control is scrolled clear of the bottom bar', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await page.getByRole('button', { name: 'Add a medicine I do not see here' }).focus()
    await page.waitForTimeout(900) // smooth scrolling
    const f = (await page.getByRole('button', { name: 'Add a medicine I do not see here' }).boundingBox())!
    const bar = (await page.locator('.rv-bar').boundingBox())!
    expect(f.y + f.height).toBeLessThanOrEqual(bar.y + 1)
  })
})

for (const lang of ['en', 'ta', 'hi'])
  for (const [w, h] of [[1280, 800], [390, 800]] as const)
    test(`axe: review (folded and open cards, bar) in ${lang} at ${w}px`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h })
      await setLangInit(page, lang)
      await reviewReady(page, { imageKept: true })
      await page.goto(`/d/${DOC_ID}/review`)
      await card(page, 1).waitFor()
      await openCard(page, 0)
      await card(page, 1).getByLabel(/^(This matches|இது|यह)/).first().check().catch(() => undefined)
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
      expect(r.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}`)).toEqual([])
      if (w < 1024) {
        await page.locator('.phone-photo').getByRole('button').last().click()
        await page.locator('dialog[open]').waitFor()
        const d = await new AxeBuilder({ page }).include('dialog').withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
        expect(d.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}`)).toEqual([])
      }
    })
