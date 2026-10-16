import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { readPref, writePref } from '../lib/prefs'

type Ctx = {
  calm: boolean
  setCalm: (v: boolean) => void
  reduced: boolean // prefers-reduced-motion
  motionOk: boolean // !calm && !reduced: ambient motion, tile drift, parallax and transitions may run
  processing: boolean // a processing screen is open: the particle field pauses
  setProcessing: (v: boolean) => void
}
const MotionContext = createContext<Ctx | null>(null)

const query = () => (typeof matchMedia === 'function' ? matchMedia('(prefers-reduced-motion: reduce)') : null)

export function MotionProvider({ children }: { children: ReactNode }) {
  const [calm, setCalmState] = useState(() => readPref('calm') === '1')
  const [reduced, setReduced] = useState(() => query()?.matches ?? false)
  const [processing, setProcessing] = useState(false)
  useEffect(() => {
    const q = query()
    if (!q) return
    const on = () => setReduced(q.matches)
    q.addEventListener('change', on)
    return () => q.removeEventListener('change', on)
  }, [])
  useEffect(() => {
    document.documentElement.classList.toggle('calm', calm)
  }, [calm])
  const setCalm = useCallback((v: boolean) => {
    setCalmState(v)
    writePref('calm', v ? '1' : '0')
  }, [])
  const value = useMemo(() => ({ calm, setCalm, reduced, motionOk: !calm && !reduced, processing, setProcessing }), [calm, setCalm, reduced, processing])
  return <MotionContext.Provider value={value}>{children}</MotionContext.Provider>
}

export function useMotion(): Ctx {
  const c = useContext(MotionContext)
  if (!c) throw new Error('useMotion needs MotionProvider')
  return c
}

/** Call from a processing screen (Phase 6b flow): the particle field stays paused while it is mounted. */
export function useProcessingScreen(): void {
  const { setProcessing } = useMotion()
  useEffect(() => {
    setProcessing(true)
    return () => setProcessing(false)
  }, [setProcessing])
}
