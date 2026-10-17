import { useRef, type CSSProperties } from 'react'
import { useMotion } from '../ambient/motion'
import { tiltFor } from '../ambient/pointer'
import { Icon, type IconName } from './icons'
import { Photo, Tile, type TilePattern, type TileTone } from './Photo'

type Cell = { x: number; y: number; w: number; h: number; tone: TileTone; pattern?: TilePattern; icon?: IconName; photo?: string; dx: number; dy: number; dur: number; delay: number }

/* Hero composition: 15 rounded tiles of different sizes on a 100 x 110 board (percent coordinates). Photo tiles fall back
 * to designed placeholder tiles when a photograph is missing. Drift is translate-only CSS; tilt is a small rotation. */
const CELLS: Cell[] = [
  { x: 0, y: 0, w: 44, h: 34, tone: 'pine', photo: 'leaves', dx: 8, dy: 6, dur: 22, delay: 0 },
  { x: 46, y: 0, w: 26, h: 20, tone: 'pine', photo: 'breakfast', dx: -6, dy: 8, dur: 18, delay: -4 },
  { x: 74, y: 0, w: 26, h: 26, tone: 'sage', pattern: 'grain', icon: 'leaf', dx: 7, dy: -7, dur: 25, delay: -9 },
  { x: 46, y: 22, w: 12, h: 14, tone: 'terracotta', pattern: 'grain', dx: 5, dy: 6, dur: 16, delay: -2 },
  { x: 60, y: 22, w: 12, h: 14, tone: 'mist', pattern: 'dots', dx: -5, dy: 5, dur: 20, delay: -7 },
  { x: 74, y: 28, w: 26, h: 20, tone: 'paper', icon: 'calendar', dx: -8, dy: 4, dur: 23, delay: -12 },
  { x: 0, y: 36, w: 20, h: 28, tone: 'pine', photo: 'stethoscope', dx: 6, dy: -8, dur: 21, delay: -5 },
  { x: 22, y: 36, w: 30, h: 28, tone: 'pine', photo: 'water', dx: -7, dy: 7, dur: 26, delay: -14 },
  { x: 54, y: 38, w: 18, h: 14, tone: 'sage', pattern: 'lines', dx: 6, dy: 5, dur: 17, delay: -1 },
  { x: 54, y: 54, w: 18, h: 24, tone: 'pine', pattern: 'dots', icon: 'clock', dx: -6, dy: -6, dur: 24, delay: -10 },
  { x: 74, y: 50, w: 26, h: 28, tone: 'mist', pattern: 'arches', icon: 'document', dx: 8, dy: 7, dur: 19, delay: -6 },
  { x: 0, y: 66, w: 34, h: 44, tone: 'pine', photo: 'linen', dx: 7, dy: -6, dur: 27, delay: -16 },
  { x: 36, y: 66, w: 16, h: 16, tone: 'paper', pattern: 'lines', icon: 'pill', dx: -5, dy: 6, dur: 15, delay: -3 },
  { x: 36, y: 84, w: 16, h: 26, tone: 'sage', pattern: 'grain', icon: 'search', dx: 6, dy: 5, dur: 22, delay: -8 },
  { x: 54, y: 80, w: 46, h: 30, tone: 'pine', photo: 'clipboard', dx: -8, dy: -5, dur: 28, delay: -11 },
]

export function Mosaic() {
  const { motionOk } = useMotion()
  const board = useRef<HTMLDivElement>(null)
  const raf = useRef(0)

  const reset = () =>
    board.current?.querySelectorAll<HTMLElement>('.mosaic-cell').forEach((c) => {
      c.style.setProperty('--rx', '0deg')
      c.style.setProperty('--ry', '0deg')
    })
  const onMove = (e: React.PointerEvent) => {
    if (!motionOk || e.pointerType !== 'mouse' || raf.current) return
    const p = { x: e.clientX, y: e.clientY }
    raf.current = requestAnimationFrame(() => {
      raf.current = 0
      board.current?.querySelectorAll<HTMLElement>('.mosaic-cell').forEach((c) => {
        const r = c.getBoundingClientRect()
        const t = tiltFor({ x: r.left + r.width / 2, y: r.top + r.height / 2 }, p, 320, 5)
        c.style.setProperty('--rx', `${t.rx.toFixed(2)}deg`)
        c.style.setProperty('--ry', `${t.ry.toFixed(2)}deg`)
      })
    })
  }

  return (
    <div ref={board} className="mosaic" aria-hidden="true" onPointerMove={onMove} onPointerLeave={reset}>
      {CELLS.map((c, i) => (
        <div
          key={i}
          className="mosaic-cell"
          style={{ left: `${c.x}%`, top: `${(c.y / 110) * 100}%`, width: `${c.w}%`, height: `${(c.h / 110) * 100}%`, '--dx': `${c.dx}px`, '--dy': `${c.dy}px`, '--dur': `${c.dur}s`, '--delay': `${c.delay}s` } as CSSProperties}
        >
          <Tile tone={c.tone} pattern={c.pattern ?? 'none'} className="mosaic-tile">
            {c.photo ? <Photo name={c.photo} alt="" missingLabel="" eager sizes="(min-width: 64rem) 20vw, 50vw" /> : null}
            {c.icon ? <Icon name={c.icon} size={c.w > 20 ? 44 : 32} /> : null}
          </Tile>
        </div>
      ))}
    </div>
  )
}
