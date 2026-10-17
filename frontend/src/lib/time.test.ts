import { describe, expect, it } from 'vitest'
import { localDate, nextDose, validTimes } from './time'

describe('schedule time helpers', () => {
  it('formats the local date', () => expect(localDate(new Date(2026, 9, 7, 23, 59))).toBe('2026-10-07'))
  it('finds the next unlogged dose today', () => {
    const slots = [{ time: '08:30' }, { time: '13:00' }, { time: '20:30' }]
    const now = new Date(2026, 9, 7, 9, 0)
    expect(nextDose(slots, now, () => false)?.time).toBe('13:00')
    expect(nextDose(slots, now, (s) => s.time === '13:00')?.time).toBe('20:30')
    expect(nextDose(slots, new Date(2026, 9, 7, 22, 0), () => false)).toBeNull()
  })
  it('validates times like the API: HH:MM, unique, 1 to 6', () => {
    expect(validTimes(['08:00', '20:00'])).toBe(true)
    expect(validTimes([])).toBe(false)
    expect(validTimes(['8:00'])).toBe(false)
    expect(validTimes(['24:00'])).toBe(false)
    expect(validTimes(['08:00', '08:00'])).toBe(false)
    expect(validTimes(['01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00'])).toBe(false)
  })
})
