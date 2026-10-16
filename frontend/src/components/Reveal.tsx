import { useEffect, useRef, useState, type ElementType, type ReactNode } from 'react'
import { useMotion } from '../ambient/motion'

/** Fades and lifts its children in once, when they scroll into view. Plain and visible when motion is off. */
export function Reveal({ children, as: Tag = 'div', className = '', delay = 0 }: { children: ReactNode; as?: ElementType; className?: string; delay?: number }) {
  const { motionOk } = useMotion()
  const ref = useRef<HTMLElement>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!motionOk || !el) return
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setSeen(true)
          io.disconnect()
        }
      },
      { rootMargin: '0px 0px -8% 0px' },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [motionOk])
  const state = !motionOk ? '' : seen ? 'reveal reveal-in' : 'reveal'
  return (
    <Tag ref={ref} className={`${state} ${className}`.trim()} style={delay ? { transitionDelay: `${delay}ms` } : undefined}>
      {children}
    </Tag>
  )
}
