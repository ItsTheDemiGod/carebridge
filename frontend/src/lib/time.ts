/* Local-date helpers for the schedule (the backend treats server local time as the user's local time in this local-first prototype). */
export const pad = (n: number) => String(n).padStart(2, '0')
export const localDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
export const hhmm = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`
export const addDays = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)
export const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/

/** The first slot at or after `now` today that has no logged event, else null. */
export function nextDose<T extends { time: string }>(slots: T[], now: Date, done: (s: T) => boolean): T | null {
  const t = hhmm(now)
  return [...slots].sort((a, b) => a.time.localeCompare(b.time)).find((s) => s.time >= t && !done(s)) ?? null
}

/** Valid, unique HH:MM list of at most 6 (the API rule). */
export const validTimes = (times: string[]) => times.length >= 1 && times.length <= 6 && new Set(times).size === times.length && times.every((x) => HHMM.test(x))
