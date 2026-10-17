import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextDelay, startPolling, type Visibility } from './poll'

beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())
const visible = (): Visibility & { set: (h: boolean) => void } => {
  let hidden = false
  const cbs = new Set<() => void>()
  return { hidden: () => hidden, onChange: (cb) => (cbs.add(cb), () => cbs.delete(cb)), set: (h) => ((hidden = h), cbs.forEach((c) => c())) }
}

describe('polling', () => {
  it('backs off from 1.5 s to a 5 s cap', () => {
    const ds = [1500]
    for (let i = 0; i < 6; i++) ds.push(nextDelay(ds[i]))
    expect(ds.slice(0, 3)).toEqual([1500, 2100, 2940])
    expect(Math.max(...ds)).toBe(5000)
  })
  it('stops on a terminal value', async () => {
    let n = 0
    const seen: number[] = []
    startPolling({ fetch: async () => ++n, isDone: (v) => v === 3, onValue: (v) => seen.push(v), onError: () => true, visibility: visible() })
    await vi.advanceTimersByTimeAsync(60_000)
    expect(seen).toEqual([1, 2, 3])
  })
  it('keeps polling after an error only when asked, and stops otherwise', async () => {
    let n = 0
    startPolling({ fetch: async () => { n++; throw new Error('x') }, isDone: () => false, onValue: () => {}, onError: () => n < 3, visibility: visible() })
    await vi.advanceTimersByTimeAsync(60_000)
    expect(n).toBe(3)
  })
  it('pauses while the tab is hidden and resumes at once when visible', async () => {
    const v = visible()
    let n = 0
    startPolling({ fetch: async () => ++n, isDone: () => false, onValue: () => {}, onError: () => true, visibility: v })
    await vi.advanceTimersByTimeAsync(100)
    expect(n).toBe(1)
    v.set(true)
    await vi.advanceTimersByTimeAsync(30_000)
    expect(n).toBe(1) // the next tick found the tab hidden and paused
    v.set(false)
    await vi.advanceTimersByTimeAsync(10)
    expect(n).toBe(2)
  })
  it('stop() aborts the request and prevents further ticks', async () => {
    let aborted = false
    let n = 0
    const stop = startPolling({ fetch: (sig) => new Promise<number>((res) => { n++; sig.addEventListener('abort', () => (aborted = true)); setTimeout(() => res(n), 50) }), isDone: () => false, onValue: () => {}, onError: () => true, visibility: visible() })
    await vi.advanceTimersByTimeAsync(10)
    stop()
    await vi.advanceTimersByTimeAsync(60_000)
    expect([aborted, n]).toEqual([true, 1])
  })
})
