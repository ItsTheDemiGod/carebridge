/* Pure logic for the particle field (no DOM): caps, stepping, linking and the pause rule. */

export type Particle = { x: number; y: number; vx: number; vy: number; r: number; tone: 0 | 1 }
export type Pointer = { x: number; y: number } | null

export const MAX_DESKTOP = 60
export const MAX_SMALL = 24
export const SMALL_WIDTH = 768
export const MAX_LINKS = 36
export const LINK_DISTANCE = 130
export const MAX_DPR = 1.5
const MAX_SPEED = 0.35 // px per frame at 60 fps
const ATTRACT_RADIUS = 200

export const particleCap = (width: number): number => (width < SMALL_WIDTH ? MAX_SMALL : MAX_DESKTOP)
export const cappedDpr = (dpr: number): number => Math.min(Math.max(dpr, 1), MAX_DPR)

/** The loop runs only when none of the pause conditions holds. */
export function shouldRun(s: { calm: boolean; reduced: boolean; hidden: boolean; processing: boolean }): boolean {
  return !s.calm && !s.reduced && !s.hidden && !s.processing
}

export function createParticles(width: number, height: number, rng: () => number = Math.random): Particle[] {
  const n = particleCap(width)
  return Array.from({ length: n }, () => {
    const a = rng() * Math.PI * 2
    const sp = 0.08 + rng() * 0.18
    return { x: rng() * width, y: rng() * height, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, r: 1.5 + rng() * 2.5, tone: rng() < 0.7 ? 0 : 1 }
  })
}

/** Advance by dt milliseconds. Gentle pointer attraction, speed clamp, wrap at the edges. Mutates and returns the array. */
export function step(ps: Particle[], dt: number, width: number, height: number, pointer: Pointer): Particle[] {
  const k = Math.min(dt, 50) / (1000 / 60) // frames elapsed, clamped so a long pause does not teleport particles
  for (const p of ps) {
    if (pointer) {
      const dx = pointer.x - p.x
      const dy = pointer.y - p.y
      const d = Math.hypot(dx, dy)
      if (d > 1 && d < ATTRACT_RADIUS) {
        const pull = (1 - d / ATTRACT_RADIUS) * 0.004 * k
        p.vx += (dx / d) * pull
        p.vy += (dy / d) * pull
      }
    }
    const sp = Math.hypot(p.vx, p.vy)
    if (sp > MAX_SPEED) {
      p.vx = (p.vx / sp) * MAX_SPEED
      p.vy = (p.vy / sp) * MAX_SPEED
    }
    p.x += p.vx * k
    p.y += p.vy * k
    if (p.x < -10) p.x = width + 10
    else if (p.x > width + 10) p.x = -10
    if (p.y < -10) p.y = height + 10
    else if (p.y > height + 10) p.y = -10
  }
  return ps
}

/** Index pairs of particles closer than LINK_DISTANCE, at most MAX_LINKS, nearest first. */
export function links(ps: Particle[]): { a: number; b: number; d: number }[] {
  const out: { a: number; b: number; d: number }[] = []
  for (let i = 0; i < ps.length; i++)
    for (let j = i + 1; j < ps.length; j++) {
      const d = Math.hypot(ps[i].x - ps[j].x, ps[i].y - ps[j].y)
      if (d < LINK_DISTANCE) out.push({ a: i, b: j, d })
    }
  return out.sort((p, q) => p.d - q.d).slice(0, MAX_LINKS)
}
