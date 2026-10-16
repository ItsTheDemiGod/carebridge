/* Pure helpers for the cursor ring and the mosaic tilt. */
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t

/** Small rotation (degrees) for a tile whose centre is at `c` when the pointer is at `p`: zero beyond `radius`,
 *  at most `max`, leaning towards the pointer. */
export function tiltFor(c: { x: number; y: number }, p: { x: number; y: number }, radius: number, max: number): { rx: number; ry: number } {
  const dx = p.x - c.x
  const dy = p.y - c.y
  const d = Math.hypot(dx, dy)
  if (d >= radius) return { rx: 0, ry: 0 }
  const f = (1 - d / radius) * max
  const n = d || 1
  return { rx: (-dy / n) * f, ry: (dx / n) * f }
}
