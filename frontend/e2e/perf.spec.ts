import { expect, test } from '@playwright/test'
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

test('particle loop frame cost and pacing, particle cap, no WebGL (headless Chromium)', async ({ page }) => {
  await page.goto('/?perf=1', { waitUntil: 'networkidle' })
  await page.mouse.move(400, 400)
  await page.waitForTimeout(8000)
  const s = await page.evaluate(() => window.__cbStats ?? null)
  expect(s).not.toBeNull()
  const q = (a: number[], p: number) => [...a].sort((x, y) => x - y)[Math.floor(a.length * p)]
  const avg = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length
  const work = s!.work
  const frames = s!.frames.slice(5)
  console.log(`PERF particles=${s!.count} samples=${work.length} work avg=${avg(work).toFixed(3)}ms p95=${q(work, 0.95).toFixed(3)}ms | frame interval avg=${avg(frames).toFixed(2)}ms p95=${q(frames, 0.95).toFixed(2)}ms`)
  expect(s!.count).toBeLessThanOrEqual(60)
  expect(avg(work)).toBeLessThan(4)
  const dist = join(process.cwd(), 'dist', 'assets')
  const js = readdirSync(dist).filter((f) => f.endsWith('.js')).map((f) => readFileSync(join(dist, f), 'utf8')).join('\n')
  expect(/getContext\(\s*["'](webgl|webgl2|experimental-webgl)["']/.test(js)).toBe(false)
  expect(await page.evaluate(() => !!document.querySelector('canvas')?.getContext('2d'))).toBe(true)
})
