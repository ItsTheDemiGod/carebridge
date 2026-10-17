import { describe, expect, it } from 'vitest'
import type { FormularyEntry, ReviewMedicine } from '../api/types'
import { attentionCount, buildConfirmations, draftFromServer, emptyDraft, missing, schedFromMedicine, toDecision, type Draft } from './review'

const med = (over: Partial<ReviewMedicine> = {}): ReviewMedicine => ({
  index: 0, ref: 'm0', as_written: { brand: 'Netfornin', generic: null }, printed: { brand: null, generic: null }, resolved_generic: null, name_match_type: null,
  strength: '500 mg', dose: '1 tablet', form: 'tablet', route: 'oral', frequency: { times_per_day: 2, timing_label: 'after_meals', is_prn: false, original_abbreviation: 'BD PC' },
  duration_days: 5, duration_text: '5 days', source_quote: 'Tab Netfornin 500 mg BD PC x 5 days', review_level: 'must_confirm', flags: [],
  reasons: [{ id: 'unresolved_name', template_id: 'x', text: 'name', kind: 'name' }, { id: 'unusual_strength', template_id: 'y', text: 'strength', kind: 'acknowledge' }],
  interaction_ready: false, schedule_ready: false, has_exact_identity: false, allowed_actions: ['confirm_as_extracted', 'select_formulary_drug', 'not_in_list', 'remove'], current_decision: null, ...over,
})
const metformin: FormularyEntry = { id: 'metformin', generic: 'Metformin', brand_names: ['Glycomet'], available_strengths: ['500 mg'], form: 'tablet', route: 'oral', strength_as_label_option: 'as_on_my_label' }
const decided = (d: Partial<Draft>): Draft => ({ ...emptyDraft(med()), decided: true, ...d })

describe('review drafts', () => {
  it('prefills the schedule fields from the extraction but sends nothing unless touched', () => {
    expect(schedFromMedicine(med())).toEqual({ times: '2', timing: 'after_meals', days: '5' })
    const d = decided({ action: 'select_formulary_drug', formulary: metformin, strength: '500 mg', acks: ['unusual_strength'] })
    expect(toDecision(med(), d)).toEqual({ index: 0, action: 'select_formulary_drug', acknowledged_flags: ['unusual_strength'], formulary_id: 'metformin', strength_choice: '500 mg' })
  })
  it('sends schedule_edit only when the person changed it', () => {
    const d = decided({ action: 'select_formulary_drug', formulary: metformin, strength: '500 mg', acks: ['unusual_strength'], schedTouched: true, sched: { times: '3', timing: 'before_meals', days: '' } })
    expect(toDecision(med(), d)?.schedule_edit).toEqual({ times_per_day: 3, timing_label: 'before_meals', duration_days: null })
  })
  it('a name reason is cleared only through the picker; acknowledgements stay required', () => {
    expect(missing(med(), { ...emptyDraft(med()), action: 'select_formulary_drug' })).toEqual(['ack', 'formulary'])
    expect(missing(med(), { ...emptyDraft(med()), action: 'select_formulary_drug', formulary: metformin, acks: ['unusual_strength'] })).toEqual(['strength'])
    expect(missing(med(), { ...emptyDraft(med()), action: 'confirm_as_extracted', acks: ['unusual_strength'] })).toEqual([])
    expect(missing(med(), { ...emptyDraft(med()), action: 'confirm_as_extracted' })).toEqual(['ack'])
    expect(missing(med(), emptyDraft(med()))).toEqual(['action'])
  })
  it('remove and not_in_list need nothing else; the note is trimmed and capped at 80 characters', () => {
    expect(toDecision(med(), decided({ action: 'remove' }))).toEqual({ index: 0, action: 'remove' })
    expect(toDecision(med(), decided({ action: 'not_in_list', note: '  ' + 'x'.repeat(100) }))?.note).toHaveLength(80)
    expect(toDecision(med(), decided({ action: 'not_in_list' }))).toEqual({ index: 0, action: 'not_in_list' })
  })
  it('an incomplete or undecided draft is never sent', () => {
    expect(toDecision(med(), decided({ action: 'select_formulary_drug' }))).toBeNull()
    expect(toDecision(med(), { ...emptyDraft(med()), action: 'remove' })).toBeNull() // not confirmed by the button
  })
  it('a non-daily medicine never gets a schedule edit', () => {
    const m = med({ flags: ['non_daily_frequency'], reasons: [{ id: 'non_daily_frequency', template_id: 'z', text: 't', kind: 'acknowledge' }] })
    const d = decided({ action: 'confirm_as_extracted', acks: ['non_daily_frequency'], schedTouched: true, sched: { times: '1', timing: 'morning', days: '' } })
    expect(toDecision(m, d)?.schedule_edit).toBeUndefined()
  })
  it('builds the FULL set every time and counts what still needs attention', () => {
    const meds = [med(), med({ index: 1, ref: 'm1', review_level: 'none', reasons: [] }), med({ index: 2, ref: 'm2' })]
    const drafts = { 0: decided({ action: 'remove' }), 1: emptyDraft(meds[1]), 2: emptyDraft(meds[2]) }
    expect(buildConfirmations(meds, drafts, []).decisions).toEqual([{ index: 0, action: 'remove' }])
    expect(attentionCount(meds, drafts)).toBe(1) // m0 decided, m1 not must_confirm, m2 open
  })
  it('restores a stored decision after a reload', () => {
    const m = med({ current_decision: { index: 0, action: 'not_in_list', note: 'cream' } })
    const d = draftFromServer(m, null)
    expect([d.action, d.note, d.decided]).toEqual(['not_in_list', 'cream', true])
  })
})
