import { useEffect, useRef, useState } from 'react'
import { useMotion } from './motion'
import { lerp } from './pointer'

const INTERACTIVE = 'a, button, input, textarea, select, summary, label, [role="button"]'

/* A dot plus a lagging ring. Only for (pointer: fine) and no reduced motion / calm mode. The native cursor stays
 * visible and the ring never takes pointer events. The loop runs only while the ring is catching up. */
export function CursorRing() {
  const { motionOk } = useMotion()
  const [fine, setFine] = useState(() => matchMedia('(pointer: fine)').matches)
  const dot = useRef<HTMLDivElement>(null)
  const ring = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const q = matchMedia('(pointer: fine)')
    const on = () => setFine(q.matches)
    q.addEventListener('change', on)
    return () => q.removeEventListener('change', on)
  }, [])

  const active = motionOk && fine
  useEffect(() => {
    const d = dot.current
    const r = ring.current
    if (!active || !d || !r) return
    let tx = -100, ty = -100, rx = -100, ry = -100, raf = 0
    const draw = () => {
      rx = lerp(rx, tx, 0.18)
      ry = lerp(ry, ty, 0.18)
      r.style.transform = `translate3d(${rx}px,${ry}px,0)`
      raf = Math.abs(tx - rx) + Math.abs(ty - ry) > 0.3 ? requestAnimationFrame(draw) : 0
    }
    const onMove = (e: PointerEvent) => {
      tx = e.clientX
      ty = e.clientY
      if (rx === -100) {
        rx = tx
        ry = ty
      }
      d.style.transform = `translate3d(${tx}px,${ty}px,0)`
      d.dataset.show = r.dataset.show = 'true'
      r.dataset.hover = String(!!(e.target as Element | null)?.closest?.(INTERACTIVE))
      if (!raf) raf = requestAnimationFrame(draw)
    }
    const onLeave = () => (d.dataset.show = r.dataset.show = 'false')
    addEventListener('pointermove', onMove, { passive: true })
    document.addEventListener('pointerleave', onLeave)
    return () => {
      cancelAnimationFrame(raf)
      removeEventListener('pointermove', onMove)
      document.removeEventListener('pointerleave', onLeave)
    }
  }, [active])

  if (!active) return null
  return (
    <>
      <div ref={ring} className="cursor-ring" aria-hidden="true" data-show="false" data-hover="false">
        <span />
      </div>
      <div ref={dot} className="cursor-dot" aria-hidden="true" data-show="false" />
    </>
  )
}
