/* Polling with setTimeout and backoff (1.5 s growing to 5 s). Stops on a terminal value, pauses while the tab is hidden, aborts on stop(). */
export type Visibility = { hidden: () => boolean; onChange: (cb: () => void) => () => void }

export const browserVisibility: Visibility = {
  hidden: () => typeof document !== 'undefined' && document.hidden,
  onChange: (cb) => {
    document.addEventListener('visibilitychange', cb)
    return () => document.removeEventListener('visibilitychange', cb)
  },
}

export type PollOptions<T> = {
  fetch: (signal: AbortSignal) => Promise<T>
  isDone: (v: T) => boolean
  onValue: (v: T) => void
  /** return true to keep polling after an error (network blip), false to stop */
  onError: (e: unknown) => boolean
  startMs?: number
  capMs?: number
  factor?: number
  visibility?: Visibility
}

export function nextDelay(current: number, cap = 5000, factor = 1.4): number {
  return Math.min(cap, Math.round(current * factor))
}

/** Returns stop(). The first request is made immediately. */
export function startPolling<T>(o: PollOptions<T>): () => void {
  const vis = o.visibility ?? browserVisibility
  const ctl = new AbortController()
  let timer: ReturnType<typeof setTimeout> | undefined
  let delay = o.startMs ?? 1500
  let waiting = false // paused because the tab is hidden
  let running = false

  const tick = async () => {
    timer = undefined
    if (ctl.signal.aborted) return
    if (vis.hidden()) {
      waiting = true
      return
    }
    running = true
    try {
      const v = await o.fetch(ctl.signal)
      if (ctl.signal.aborted) return
      o.onValue(v)
      if (o.isDone(v)) return
    } catch (e) {
      if (ctl.signal.aborted || !o.onError(e)) return
    } finally {
      running = false
    }
    delay = nextDelay(delay, o.capMs, o.factor)
    timer = setTimeout(tick, delay)
  }

  const off = vis.onChange(() => {
    if (!vis.hidden() && waiting && !running) {
      waiting = false
      void tick()
    }
  })
  void tick()
  return () => {
    ctl.abort()
    if (timer) clearTimeout(timer)
    off()
  }
}
