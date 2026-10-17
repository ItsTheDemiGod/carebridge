import { describe, expect, it } from 'vitest'
import type { ReviewMedicine } from '../api/types'
import { emptyDraft, orderMedicines, readParts, statusOf, type Draft } from './review'

const med = (index: number, level: ReviewMedicine['review_level'], over: Partial<ReviewMedicine> = {}): ReviewMedicine =>
  ({ index, ref: `m${index}`, review_level: level, reasons: [], flags: [], allowed_actions: ['confirm_as_extracted', 'select_formulary_drug', 'not_in_list', 'remove'], as_written: { brand: 'X', generic: null }, source_quote: 'q', strength: null, dose: null, duration_days: null, duration_text: null, frequency: { times_per_day: null, timing_label: 'unspecified', original_abbreviation: null, is_prn: false }, has_exact_identity: true, current_decision: null, ...over }) as unknown as ReviewMedicine
const decided = (m: ReviewMedicine): Draft => ({ ...emptyDraft(m), action: 'confirm_as_extracted', decided: true })

describe('statusOf', () => {
  it('must_confirm without a decision needs your check; with a complete decision it is checked by you', () => {
    const m = med(0, 'must_confirm')
    expect(statusOf(m, emptyDraft(m))).toBe('attention')
    expect(statusOf(m, decided(m))).toBe('checked')
  })
  it('a decision that is not complete (pending acknowledgement) is still needs-your-check', () => {
    const m = med(0, 'must_confirm', { reasons: [{ id: 'unusual_strength', kind: 'acknowledge', text: 't' }] } as Partial<ReviewMedicine>)
    expect(statusOf(m, decided(m))).toBe('attention')
  })
  it('note and none levels need no action until the person decides', () => {
    for (const l of ['note', 'none'] as const) expect(statusOf(med(1, l), undefined)).toBe('noaction')
  })
  it('fails closed: the server saying it is still open overrides a local decision', () => {
    const m = med(0, 'must_confirm')
    expect(statusOf(m, decided(m), { unresolved: ['x'], review_level: 'note' })).toBe('attention')
    expect(statusOf(m, decided(m), { unresolved: [], review_level: 'must_confirm' })).toBe('attention')
    expect(statusOf(m, decided(m), { unresolved: [], review_level: 'none' })).toBe('checked')
  })
})

describe('orderMedicines', () => {
  const meds = [med(0, 'none'), med(1, 'must_confirm'), med(2, 'note'), med(3, 'must_confirm'), med(4, 'none')]
  it('needs-attention first, then notes, then the rest, each in document order', () => {
    expect(orderMedicines(meds, 'attention').map((m) => m.index)).toEqual([1, 3, 2, 0, 4])
  })
  it('document order restores the extracted order, and never mutates the input', () => {
    expect(orderMedicines(meds, 'document').map((m) => m.index)).toEqual([0, 1, 2, 3, 4])
    expect(meds.map((m) => m.index)).toEqual([0, 1, 2, 3, 4])
  })
})

describe('readParts', () => {
  it('one frequency phrase: the abbreviation is used only when no number was read', () => {
    const f = (o: object) => readParts(med(0, 'none', { frequency: { times_per_day: null, timing_label: 'unspecified', original_abbreviation: null, is_prn: false, ...o } as ReviewMedicine['frequency'] }))
    expect(f({ times_per_day: 2, original_abbreviation: 'BD', timing_label: 'after_meals' })).toMatchObject({ times: 2, timing: 'after_meals', abbreviation: null })
    expect(f({ original_abbreviation: 'QOD' })).toMatchObject({ times: null, abbreviation: 'QOD' })
    expect(f({ is_prn: true })).toMatchObject({ times: 'as_needed' })
  })
  it('keeps what was not read as null so the screen can say so', () => {
    expect(readParts(med(0, 'none'))).toMatchObject({ strength: null, dose: null, days: null, durationText: null })
  })
})
