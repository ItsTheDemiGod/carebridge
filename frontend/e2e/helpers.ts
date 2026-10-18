import type { BrowserContext, Page } from '@playwright/test'

export const ROUTES = ['/', '/how-it-works', '/how-we-tested-it', '/privacy', '/start', '/no-such-page']
export const LANGS = ['en', 'ta', 'hi'] as const

export async function setLang(ctx: BrowserContext, lang: string) {
  await ctx.addInitScript((l) => localStorage.setItem('carebridge.language', l), lang)
}

/** Collects console errors and page errors. */
export function watch(page: Page) {
  const errors: string[] = []
  page.on('console', (m) => m.type() === 'error' && errors.push(`console: ${m.text()}`))
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
  return errors
}

export const blockApi = (page: Page) => page.route('**/api/**', (r) => r.abort())
