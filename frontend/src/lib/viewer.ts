/* Geometry of the photo viewer: the image is laid out fit-to-width (zoom 1), scaled from its top-left corner, and moved by a pixel offset. */
export type Box = { w: number; h: number }
export type Pos = { x: number; y: number }
export const ZOOM_MIN = 1
export const ZOOM_MAX = 5

export const baseSize = (frame: Box, natural: Box): Box => ({ w: frame.w, h: natural.w ? (frame.w * natural.h) / natural.w : 0 })

/** Keep the image covering the frame; a dimension smaller than the frame is centred, so there is never an empty gap on one side only. */
export function clampPan(pos: Pos, zoom: number, frame: Box, natural: Box): Pos {
  const b = baseSize(frame, natural)
  const sw = b.w * zoom
  const sh = b.h * zoom
  const fit = (p: number, s: number, f: number) => (s <= f ? (f - s) / 2 : Math.min(0, Math.max(f - s, p)))
  return { x: fit(pos.x, sw, frame.w), y: fit(pos.y, sh, frame.h) }
}

/** Zoom keeping the image point under `anchor` (frame coordinates) where it is. */
export function zoomAbout(pos: Pos, zoom: number, next: number, anchor: Pos, frame: Box, natural: Box): { zoom: number; pos: Pos } {
  const z = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, next))
  const k = z / zoom
  return { zoom: z, pos: clampPan({ x: anchor.x - (anchor.x - pos.x) * k, y: anchor.y - (anchor.y - pos.y) * k }, z, frame, natural) }
}
