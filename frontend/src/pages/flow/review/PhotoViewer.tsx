import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Icon } from '../../../components/icons'
import { useT } from '../../../i18n/I18n'
import { baseSize, clampPan, zoomAbout, ZOOM_MAX, ZOOM_MIN, type Box, type Pos } from '../../../lib/viewer'

const STEP = 0.5
const PAN = 48

/** The person's own photo, fit to the width of its pane, with zoom, reset, drag to pan and (on touch) pinch. It fills the height it is given.
 *  Keyboard (frame focused): arrows pan, plus and minus zoom, 0 resets. The photo is a Blob URL held in memory only. */
export function PhotoViewer({ url, className = '' }: { url: string; className?: string }) {
  const { t } = useT()
  const frameRef = useRef<HTMLDivElement>(null)
  const [frame, setFrame] = useState<Box>({ w: 0, h: 0 })
  const [natural, setNatural] = useState<Box>({ w: 0, h: 0 })
  const [zoom, setZoom] = useState(1)
  const [pos, setPos] = useState<Pos>({ x: 0, y: 0 })
  const pointers = useRef(new Map<number, Pos>())
  const pinch = useRef<{ dist: number; zoom: number } | null>(null)

  useLayoutEffect(() => {
    const el = frameRef.current
    if (!el) return
    const measure = () => setFrame({ w: el.clientWidth, h: el.clientHeight })
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  // keep the image inside its frame whenever the frame or the image size changes
  useEffect(() => {
    if (frame.w && natural.w) setPos((p) => clampPan(p, zoom, frame, natural))
  }, [frame, natural, zoom])

  const ready = frame.w > 0 && natural.w > 0
  const center: Pos = { x: frame.w / 2, y: frame.h / 2 }
  const zoomTo = useCallback(
    (next: number, anchor: Pos = center) => {
      if (!ready) return
      const r = zoomAbout(pos, zoom, next, anchor, frame, natural)
      setZoom(r.zoom)
      setPos(r.pos)
    },
    [ready, pos, zoom, frame, natural, center.x, center.y], // eslint-disable-line react-hooks/exhaustive-deps
  )
  const panBy = (dx: number, dy: number) => ready && setPos((p) => clampPan({ x: p.x + dx, y: p.y + dy }, zoom, frame, natural))
  const reset = () => {
    setZoom(1)
    setPos(clampPan({ x: 0, y: 0 }, 1, frame, natural))
  }
  const base = ready ? baseSize(frame, natural) : { w: 0, h: 0 }

  return (
    <div className={`photo-viewer ${className}`.trim()}>
      <div className="pv-tools" role="group" aria-label={t('ui.flow.photo.tools')}>
        <button type="button" className="pv-btn" onClick={() => zoomTo(zoom - STEP)} disabled={zoom <= ZOOM_MIN} aria-label={t('ui.flow.photo.zoom_out')} title={t('ui.flow.photo.zoom_out')}>
          <Icon name="zoomout" size={22} />
        </button>
        <button type="button" className="pv-btn" onClick={() => zoomTo(zoom + STEP)} disabled={zoom >= ZOOM_MAX} aria-label={t('ui.flow.photo.zoom_in')} title={t('ui.flow.photo.zoom_in')}>
          <Icon name="zoomin" size={22} />
        </button>
        <button type="button" className="pv-btn" onClick={reset} aria-label={t('ui.flow.photo.reset')} title={t('ui.flow.photo.reset')}>
          <Icon name="reset" size={22} />
        </button>
      </div>
      <div
        ref={frameRef}
        className="pv-frame"
        tabIndex={0}
        role="group"
        aria-label={t('ui.flow.photo.label')}
        aria-describedby="pv-help"
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') panBy(PAN, 0)
          else if (e.key === 'ArrowRight') panBy(-PAN, 0)
          else if (e.key === 'ArrowUp') panBy(0, PAN)
          else if (e.key === 'ArrowDown') panBy(0, -PAN)
          else if (e.key === '+' || e.key === '=') zoomTo(zoom + STEP)
          else if (e.key === '-') zoomTo(zoom - STEP)
          else if (e.key === '0') reset()
          else return
          e.preventDefault()
        }}
        onPointerDown={(e) => {
          pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
          try {
            e.currentTarget.setPointerCapture(e.pointerId)
          } catch {
            /* a pointer that is already gone: nothing to capture */
          }
          if (pointers.current.size === 2) {
            const [a, b] = [...pointers.current.values()]
            pinch.current = { dist: Math.hypot(a.x - b.x, a.y - b.y) || 1, zoom }
          }
        }}
        onPointerMove={(e) => {
          const prev = pointers.current.get(e.pointerId)
          if (!prev) return
          const now = { x: e.clientX, y: e.clientY }
          pointers.current.set(e.pointerId, now)
          if (pointers.current.size === 2 && pinch.current) {
            const [a, b] = [...pointers.current.values()]
            const r = frameRef.current!.getBoundingClientRect()
            zoomTo((pinch.current.zoom * Math.hypot(a.x - b.x, a.y - b.y)) / pinch.current.dist, { x: (a.x + b.x) / 2 - r.left, y: (a.y + b.y) / 2 - r.top })
          } else if (pointers.current.size === 1) panBy(now.x - prev.x, now.y - prev.y)
        }}
        onPointerUp={(e) => {
          pointers.current.delete(e.pointerId)
          if (pointers.current.size < 2) pinch.current = null
        }}
        onPointerCancel={(e) => {
          pointers.current.delete(e.pointerId)
          pinch.current = null
        }}
      >
        <img
          src={url}
          alt={t('ui.flow.photo.alt')}
          draggable={false}
          onLoad={(e) => setNatural({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
          style={{ width: base.w || '100%', height: base.h || 'auto', transform: `translate(${pos.x}px, ${pos.y}px) scale(${zoom})`, visibility: ready ? 'visible' : 'hidden' }}
        />
      </div>
      <p className="small muted pv-note">
        <Icon name="info" size={16} /> <span>{t('ui.flow.rv.paper_ref')}</span>
      </p>
      <p id="pv-help" className="small muted">{t('ui.flow.photo.help')}</p>
    </div>
  )
}
