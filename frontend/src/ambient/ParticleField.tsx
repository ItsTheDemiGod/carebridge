import { useEffect, useRef, useState } from 'react'
import { useMotion } from './motion'
import { LINK_DISTANCE, cappedDpr, createParticles, links, particleCap, shouldRun, step, type Particle, type Pointer } from './particles'

/* One fixed canvas behind the content. Canvas 2D only. Paused when the tab is hidden, in calm mode, under reduced
 * motion and while a processing screen is open. Dev (or ?perf=1) collects frame-time stats on window.__cbStats. */
export type Stats = { count: number; frames: number[]; work: number[] }
declare global {
  interface Window {
    __cbStats?: Stats
  }
}
const wantStats = () => import.meta.env.DEV || location.search.includes('perf=1')
const rgb = (hex: string) => {
  const h = hex.trim().replace('#', '')
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)).join(',')
}

export function ParticleField() {
  const { calm, reduced, processing } = useMotion()
  const ref = useRef<HTMLCanvasElement>(null)
  const [hidden, setHidden] = useState(() => document.hidden)
  useEffect(() => {
    const on = () => setHidden(document.hidden)
    document.addEventListener('visibilitychange', on)
    return () => document.removeEventListener('visibilitychange', on)
  }, [])
  const run = shouldRun({ calm, reduced, hidden, processing })
  const off = calm || reduced // fully off (cleared), as opposed to merely paused

  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    canvas.dataset.running = String(run)
    let w = innerWidth
    let h = innerHeight
    let dpr = cappedDpr(devicePixelRatio)
    const size = () => {
      w = innerWidth
      h = innerHeight
      dpr = cappedDpr(devicePixelRatio)
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    size()
    if (off) {
      ctx.clearRect(0, 0, w, h)
      return
    }
    const cs = getComputedStyle(document.documentElement)
    const sage = rgb(cs.getPropertyValue('--sage'))
    const pine = rgb(cs.getPropertyValue('--pine'))
    let ps: Particle[] = createParticles(w, h)
    let pointer: Pointer = null
    const onMove = (e: PointerEvent) => (pointer = { x: e.clientX, y: e.clientY })
    const onLeave = () => (pointer = null)
    let resizeTimer = 0
    const onResize = () => {
      clearTimeout(resizeTimer)
      resizeTimer = window.setTimeout(() => {
        size()
        if (ps.length !== particleCap(w)) ps = createParticles(w, h)
      }, 120)
    }
    addEventListener('pointermove', onMove, { passive: true })
    document.addEventListener('pointerleave', onLeave)
    addEventListener('resize', onResize)

    const stats: Stats | null = wantStats() ? { count: ps.length, frames: [], work: [] } : null
    if (stats) window.__cbStats = stats
    let raf = 0
    let last = performance.now()
    let n = 0
    const tick = (now: number) => {
      const dt = now - last
      last = now
      const t0 = performance.now()
      step(ps, dt, w, h, pointer)
      ctx.clearRect(0, 0, w, h)
      for (const l of links(ps)) {
        ctx.strokeStyle = `rgba(${pine},${(0.16 * (1 - l.d / LINK_DISTANCE)).toFixed(3)})`
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(ps[l.a].x, ps[l.a].y)
        ctx.lineTo(ps[l.b].x, ps[l.b].y)
        ctx.stroke()
      }
      for (const p of ps) {
        ctx.fillStyle = p.tone === 0 ? `rgba(${sage},0.6)` : `rgba(${pine},0.28)`
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fill()
      }
      if (stats) {
        stats.count = ps.length
        stats.frames.push(dt)
        stats.work.push(performance.now() - t0)
        if (stats.frames.length > 600) {
          stats.frames.shift()
          stats.work.shift()
        }
      }
      if (++n % 20 === 0) canvas.dataset.frames = String(n)
      raf = requestAnimationFrame(tick)
    }
    if (run) raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      clearTimeout(resizeTimer)
      removeEventListener('pointermove', onMove)
      document.removeEventListener('pointerleave', onLeave)
      removeEventListener('resize', onResize)
    }
  }, [run, off])

  return <canvas ref={ref} className="ambient-canvas" aria-hidden="true" data-running="false" />
}
