import { useEffect, type RefObject } from 'react'
import { useMotion } from './motion'

/** Small scroll parallax with GSAP ScrollTrigger on `[data-parallax="0.1"]` children (amount x 100 px each way).
 *  GSAP is loaded on demand, only when motion is allowed, and everything is reverted when it is not. */
export function useParallax(root: RefObject<HTMLElement | null>) {
  const { motionOk } = useMotion()
  useEffect(() => {
    if (!motionOk || !root.current) return
    let ctx: { revert: () => void } | undefined
    let cancelled = false
    void Promise.all([import('gsap'), import('gsap/ScrollTrigger')]).then(([{ gsap }, { ScrollTrigger }]) => {
      if (cancelled || !root.current) return
      gsap.registerPlugin(ScrollTrigger)
      ctx = gsap.context(() => {
        root.current!.querySelectorAll<HTMLElement>('[data-parallax]').forEach((el) => {
          const a = parseFloat(el.dataset.parallax ?? '0.1') * 100
          gsap.fromTo(el, { y: a }, { y: -a, ease: 'none', scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true } })
        })
      }, root.current)
    })
    return () => {
      cancelled = true
      ctx?.revert()
    }
  }, [motionOk, root])
}
