import { useEffect, useState } from 'react'

/* Development-only overlay: average work per frame and particle count. Compiled out of production builds. */
export function FrameMonitor() {
  const [line, setLine] = useState('')
  useEffect(() => {
    if (!import.meta.env.DEV) return
    const id = setInterval(() => {
      const s = window.__cbStats
      if (!s || !s.work.length) return setLine('')
      const avg = s.work.reduce((a, b) => a + b, 0) / s.work.length
      setLine(`particles ${s.count} | ${avg.toFixed(2)} ms work/frame`)
    }, 500)
    return () => clearInterval(id)
  }, [])
  if (!import.meta.env.DEV || !line) return null
  return (
    <div className="frame-monitor" aria-hidden="true">
      {line}
    </div>
  )
}
