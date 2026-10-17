import { describe, expect, it } from 'vitest'
import { baseSize, clampPan, zoomAbout } from './viewer'

const frame = { w: 400, h: 600 }
const portrait = { w: 1000, h: 1400 } // fit-to-width gives 400 x 560
const tall = { w: 1000, h: 2000 } // fit-to-width gives 400 x 800: taller than the frame

describe('viewer geometry', () => {
  it('fits to width', () => expect(baseSize(frame, tall)).toEqual({ w: 400, h: 800 }))
  it('centres an image that is shorter than the frame, and stops a taller one at its edges', () => {
    expect(clampPan({ x: 50, y: 50 }, 1, frame, portrait)).toEqual({ x: 0, y: 20 })
    expect(clampPan({ x: 0, y: 100 }, 1, frame, tall)).toEqual({ x: 0, y: 0 })
    expect(clampPan({ x: 0, y: -900 }, 1, frame, tall)).toEqual({ x: 0, y: -200 })
  })
  it('zoomed in, pan is limited to the scaled image', () => {
    expect(clampPan({ x: 99, y: 99 }, 2, frame, tall)).toEqual({ x: 0, y: 0 })
    expect(clampPan({ x: -999, y: -9999 }, 2, frame, tall)).toEqual({ x: -400, y: -1000 })
  })
  it('zoom keeps the anchored point in place and respects the limits', () => {
    const r = zoomAbout({ x: 0, y: 0 }, 1, 2, { x: 200, y: 300 }, frame, tall)
    expect(r.zoom).toBe(2)
    expect(r.pos).toEqual({ x: -200, y: -300 })
    expect(zoomAbout({ x: 0, y: 0 }, 1, 99, { x: 0, y: 0 }, frame, tall).zoom).toBe(5)
    expect(zoomAbout({ x: 0, y: 0 }, 1, 0.1, { x: 0, y: 0 }, frame, tall).zoom).toBe(1)
  })
})
