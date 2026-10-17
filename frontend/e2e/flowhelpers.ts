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

export const card = (page: Page, i: number) => page.locator('article.med-card').nth(i)

export async function pickDrug(page: Page, scope: ReturnType<typeof card> | Page, query: string, name: string) {
  const box = scope.getByRole('combobox', { name: /Search medicine/ })
  await box.fill(query)
  await expect(scope.getByRole('option', { name: new RegExp(name) })).toBeVisible()
  await box.press('ArrowDown')
  await box.press('Enter')
}
