import { describe, expect, it } from 'vitest'
import { LINK_DISTANCE, MAX_DESKTOP, MAX_LINKS, MAX_SMALL, cappedDpr, createParticles, links, particleCap, shouldRun, step } from './particles'
import { lerp, tiltFor } from './pointer'

const seeded = () => {
  let s = 7
  return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646
}

describe('particle caps', () => {
  it('uses at most 60 on desktop and 24 on small screens', () => {
    expect(particleCap(1440)).toBe(MAX_DESKTOP)
    expect(particleCap(767)).toBe(MAX_SMALL)
    expect(createParticles(1920, 1080, seeded())).toHaveLength(60)
    expect(createParticles(390, 800, seeded())).toHaveLength(24)
    expect(MAX_DESKTOP).toBeLessThanOrEqual(60)
  })
  it('caps devicePixelRatio at 1.5', () => {
    expect([1, 1.25, 2, 3].map(cappedDpr)).toEqual([1, 1.25, 1.5, 1.5])
  })
})

describe('step', () => {
  it('keeps particles inside the wrapped area and never exceeds the speed clamp', () => {
    const ps = createParticles(800, 600, seeded())
    for (let i = 0; i < 600; i++) step(ps, 16.7, 800, 600, { x: 400, y: 300 })
    for (const p of ps) {
      expect(p.x).toBeGreaterThanOrEqual(-10)
      expect(p.x).toBeLessThanOrEqual(810)
      expect(Math.hypot(p.vx, p.vy)).toBeLessThanOrEqual(0.3501)
    }
  })
  it('attracts gently towards the pointer and clamps a huge dt', () => {
    const p = [{ x: 100, y: 100, vx: 0, vy: 0, r: 2, tone: 0 as const }]
    step(p, 16.7, 800, 600, { x: 200, y: 100 })
    expect(p[0].vx).toBeGreaterThan(0)
    const q = [{ x: 100, y: 100, vx: 0.3, vy: 0, r: 2, tone: 0 as const }]
    step(q, 100000, 800, 600, null)
    expect(q[0].x).toBeLessThan(100 + 0.35 * 4)
  })
})

describe('links', () => {
  it('links only close pairs and caps the count', () => {
    expect(links([{ x: 0, y: 0, vx: 0, vy: 0, r: 1, tone: 0 }, { x: LINK_DISTANCE + 5, y: 0, vx: 0, vy: 0, r: 1, tone: 0 }])).toEqual([])
    const crowd = Array.from({ length: 30 }, (_, i) => ({ x: i, y: 0, vx: 0, vy: 0, r: 1, tone: 0 as const }))
    expect(links(crowd)).toHaveLength(MAX_LINKS)
  })
})

describe('pause conditions', () => {
  const on = { calm: false, reduced: false, hidden: false, processing: false }
  it('runs only when nothing pauses it', () => {
    expect(shouldRun(on)).toBe(true)
    for (const k of Object.keys(on) as (keyof typeof on)[]) expect(shouldRun({ ...on, [k]: true })).toBe(false)
  })
})

describe('pointer helpers', () => {
  it('lerp moves a fraction of the way', () => {
    expect(lerp(0, 10, 0.2)).toBe(2)
  })
  it('tilt is zero far away, bounded near, and points towards the pointer', () => {
    expect(tiltFor({ x: 0, y: 0 }, { x: 1000, y: 0 }, 300, 4)).toEqual({ rx: 0, ry: 0 })
    const near = tiltFor({ x: 0, y: 0 }, { x: 50, y: 0 }, 300, 4)
    expect(near.ry).toBeGreaterThan(0)
    expect(Math.abs(near.ry)).toBeLessThanOrEqual(4)
    expect(tiltFor({ x: 0, y: 0 }, { x: 0, y: -50 }, 300, 4).rx).toBeGreaterThan(0)
  })
})
