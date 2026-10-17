import { useRef, useState } from 'react'
import { Button } from '../../../components/Button'
import { useT } from '../../../i18n/I18n'

const MIN = 1
const MAX = 4

/** The person's own photo with zoom and pan, so each medicine can be compared with the source. Keyboard: arrows pan, + and - zoom, 0 resets. */
export function PhotoViewer({ url }: { url: string }) {
  const { t } = useT()
  const [zoom, setZoom] = useState(1)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const drag = useRef<{ x: number; y: number } | null>(null)
  const clamp = (z: number, p: { x: number; y: number }) => {
    const lim = ((z - 1) * 100) / 2 // percent of the box that may be panned
    return { x: Math.max(-lim, Math.min(lim, p.x)), y: Math.max(-lim, Math.min(lim, p.y)) }
  }
  const setZ = (z: number) => {
    const nz = Math.max(MIN, Math.min(MAX, z))
    setZoom(nz)
    setPos((p) => clamp(nz, p))
  }
  const pan = (dx: number, dy: number) => setPos((p) => clamp(zoom, { x: p.x + dx, y: p.y + dy }))
  return (
    <div className="photo-viewer">
      <div className="pv-tools" role="group" aria-label={t('ui.flow.photo.tools')}>
        <Button variant="secondary" onClick={() => setZ(zoom - 0.5)} disabled={zoom <= MIN} aria-label={t('ui.flow.photo.zoom_out')}>−</Button>
        <Button variant="secondary" onClick={() => setZ(zoom + 0.5)} disabled={zoom >= MAX} aria-label={t('ui.flow.photo.zoom_in')}>+</Button>
        <Button variant="quiet" onClick={() => (setZoom(1), setPos({ x: 0, y: 0 }))}>{t('ui.flow.photo.reset')}</Button>
      </div>
      <div
        className="pv-frame"
        tabIndex={0}
        role="group"
        aria-label={t('ui.flow.photo.label')}
        aria-describedby="pv-help"
        onKeyDown={(e) => {
          const step = 6
          if (e.key === 'ArrowLeft') pan(step, 0)
          else if (e.key === 'ArrowRight') pan(-step, 0)
          else if (e.key === 'ArrowUp') pan(0, step)
          else if (e.key === 'ArrowDown') pan(0, -step)
          else if (e.key === '+' || e.key === '=') setZ(zoom + 0.5)
          else if (e.key === '-') setZ(zoom - 0.5)
          else if (e.key === '0') (setZoom(1), setPos({ x: 0, y: 0 }))
          else return
          e.preventDefault()
        }}
        onPointerDown={(e) => {
          drag.current = { x: e.clientX, y: e.clientY }
          e.currentTarget.setPointerCapture(e.pointerId)
        }}
        onPointerMove={(e) => {
          if (!drag.current || zoom === 1) return
          const r = e.currentTarget.getBoundingClientRect()
          pan(((e.clientX - drag.current.x) / r.width) * 100, ((e.clientY - drag.current.y) / r.height) * 100)
          drag.current = { x: e.clientX, y: e.clientY }
        }}
        onPointerUp={() => (drag.current = null)}
      >
        <img src={url} alt={t('ui.flow.photo.alt')} draggable={false} style={{ transform: `translate(${pos.x}%, ${pos.y}%) scale(${zoom})` }} />
      </div>
      <p id="pv-help" className="small muted">{t('ui.flow.photo.help')}</p>
    </div>
  )
}
