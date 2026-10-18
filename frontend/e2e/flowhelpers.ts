import type { Page } from '@playwright/test'
import { expect } from '@playwright/test'
import { DOC_ID } from './fixtures'
import { mockApi, type MockOptions } from './mock'

export { DOC_ID }
export const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==', 'base64')
export const PDF = Buffer.from('%PDF-1.4\n%fake\n')

/** console and page errors; 4xx "Failed to load resource" lines are the browser logging the API statuses these tests inject on purpose */
export function watchErrors(page: Page) {
  const errors: string[] = []
  page.on('console', (m) => m.type() === 'error' && !/Failed to load resource: the server responded with a status of 4\d\d/.test(m.text()) && errors.push(`console: ${m.text()}`))
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
  return errors
}

export const setLangInit = (page: Page, lang: string) => page.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)

export async function consented(page: Page, o: MockOptions = {}) {
  return mockApi(page, { consented: true, ...o })
}

/** A document that is waiting for the person's check */
export const reviewReady = (page: Page, o: MockOptions = {}) => mockApi(page, { consented: true, docReady: true, ...o })

/** the card of the medicine with this DOCUMENT index (the list order puts needs-attention first, so the position is not the index) */
export const card = (page: Page, i: number) => page.locator('article.med-card', { has: page.locator(`#rv-h-${i}`) })
/** cards that need nothing start folded: open one with its Edit button */
export async function openCard(page: Page, i: number) {
  const t = page.locator(`#rv-toggle-${i}`)
  if ((await t.count()) && (await t.getAttribute('aria-expanded')) === 'false') await t.click()
  return card(page, i)
}

export async function pickDrug(page: Page, scope: ReturnType<typeof card> | Page, query: string, name: string) {
  const box = scope.getByRole('combobox', { name: /Search medicine/ })
  await box.fill(query)
  await expect(scope.getByRole('option', { name: new RegExp(name) })).toBeVisible()
  await box.press('ArrowDown')
  await box.press('Enter')
}

/** Opens the header menu when the header is collapsed (the menu button is visible and closed). Safe to call in the one-row layout. */
export async function openMenuIfCollapsed(page: Page) {
  const btn = page.locator('.menu-btn')
  if ((await btn.isVisible()) && (await btn.getAttribute('aria-expanded')) === 'false') await btn.click()
}

/** Presses "Delete my data" in the header the way a person does: the icon beside the Menu button when it is shown (768 px and wider, collapsed header),
 *  otherwise the text button, after opening the menu if the header is collapsed. Every spec that deletes through the header uses this. */
export async function pressDelete(page: Page) {
  const icon = page.locator('.delete-icon')
  if (await icon.isVisible()) return icon.click()
  await openMenuIfCollapsed(page)
  await page.locator('.header-menu .delete-btn, .site-header .delete-btn').first().click()
}
