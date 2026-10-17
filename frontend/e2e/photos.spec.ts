import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { setLangInit } from './flowhelpers'

const ROOT = fileURLToPath(new URL('../../', import.meta.url))
const manifest = JSON.parse(readFileSync(`${ROOT}frontend/src/photos.manifest.json`, 'utf8')) as Record<string, { credit: string; source: string }>
const attribution = readFileSync(`${ROOT}assets/ATTRIBUTION.md`, 'utf8')

test('every photograph in the manifest is credited with photographer, licence and a link, and ATTRIBUTION.md says the same', async ({ page }) => {
  await page.goto('/')
  await page.locator('.footer-credits summary').click()
  const links = await page.locator('.footer-credits a').evaluateAll((a) => a.map((e) => ({ text: (e.textContent ?? '').trim(), href: (e as HTMLAnchorElement).href })))
  expect(links.length).toBe(Object.keys(manifest).length)
  for (const [name, e] of Object.entries(manifest)) {
    expect(links, name).toContainEqual({ text: e.credit, href: e.source })
    expect(e.credit).toMatch(/, (CC0 1\.0|CC BY [\d.]+|Pexels License)$/)
    expect(attribution, `${name} in ATTRIBUTION.md`).toContain(e.source)
    expect(attribution).toContain(e.credit.split(', ')[0])
  }
  for (const a of await page.locator('.footer-credits a').all()) expect(await a.getAttribute('rel')).toContain('noreferrer')
})

test('the landing photographs use responsive WebP/JPEG sets with explicit size, alt text, and the first screen is eager', async ({ page }) => {
  await setLangInit(page, 'en')
  await page.goto('/')
  const imgs = await page.locator('.landing picture img').evaluateAll((l) =>
    l.map((i) => ({ w: i.getAttribute('width'), h: i.getAttribute('height'), alt: i.getAttribute('alt'), loading: i.getAttribute('loading'), srcset: i.getAttribute('srcset') ?? '', webp: (i.parentElement!.querySelector('source') as HTMLSourceElement | null)?.type, inMosaic: !!i.closest('.mosaic') })),
  )
  expect(imgs.length).toBeGreaterThanOrEqual(10)
  for (const i of imgs) {
    expect(Number(i.w) > 0 && Number(i.h) > 0).toBe(true)
    expect(i.alt).not.toBeNull()
    expect(i.webp).toBe('image/webp')
    expect(i.srcset).toMatch(/800w/)
    if (i.inMosaic) expect(i.loading).toBe('eager')
    else {
      expect(i.loading).toBe('lazy')
      expect(i.alt!.length, 'a photograph outside the decorative mosaic needs alt text').toBeGreaterThan(5)
    }
  }
  expect(imgs.filter((i) => i.inMosaic).length, 'about half of the mosaic picture tiles are photographs').toBeGreaterThanOrEqual(5)
})

test('hero photographs stay under 500 KB at 1440 px', async ({ browser }) => {
  const c = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await c.newPage()
  let bytes = 0
  const pending: Promise<void>[] = []
  page.on('requestfinished', (r) => { if (/\/photos\/.*-800\.webp/.test(r.url()) && r.url().match(/leaves|breakfast|stethoscope|water|linen|clipboard/)) pending.push(r.sizes().then((s) => { bytes += s.responseBodySize })) })
  await page.goto('/', { waitUntil: 'networkidle' })
  await Promise.all(pending)
  expect(bytes).toBeGreaterThan(100_000)
  expect(bytes).toBeLessThan(500_000)
  await c.close()
})
