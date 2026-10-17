/* Pure logic of the medicine review screen: drafts, what is still missing, and the full decision set sent to the API
 * (POST /confirmations REPLACES the previous set, so everything decided is always sent). No React, no text. */
import type { AddedMedicine, Confirmations, MedicineDecision, ScheduleEdit } from '../api/openapi.generated'
import { TIMING_LABELS } from '../api/openapi.generated'
import type { FormularyEntry, MedicineAction, ReviewMedicine } from '../api/types'

export type SchedDraft = { times: string; timing: string; days: string }
export type Draft = {
  action: MedicineAction | null
  formulary: FormularyEntry | null
  strength: string | null
  acks: string[]
  note: string
  sched: SchedDraft
  schedTouched: boolean
  /** the person pressed the card's confirm button (or it was restored from the server) */
  decided: boolean
}
export type AddedDraft = { key: string; formulary: FormularyEntry; strength: string; dose: string; sched: SchedDraft }

export const NOTE_MAX = 80
export const MAX_ADDED = 10
export const TIMES_CHOICES = ['1', '2', '3', '4', '5', '6', 'as_needed'] as const
export const isTiming = (x: unknown): x is ScheduleEdit['timing_label'] => (TIMING_LABELS as readonly string[]).includes(x as string)

export function schedFromMedicine(m: ReviewMedicine): SchedDraft {
  const t = m.frequency.times_per_day
  const label = m.frequency.timing_label
  return {
    times: typeof t === 'number' && t >= 1 && t <= 6 ? String(t) : m.frequency.is_prn ? 'as_needed' : '',
    timing: isTiming(label) ? label : 'unspecified',
    days: typeof m.duration_days === 'number' && m.duration_days >= 1 && m.duration_days <= 365 ? String(m.duration_days) : '',
  }
}

export const emptyDraft = (m: ReviewMedicine): Draft => ({ action: null, formulary: null, strength: null, acks: [], note: '', sched: schedFromMedicine(m), schedTouched: false, decided: false })

/** Rebuild a draft from the decision the server stored (page reload). The formulary entry is filled in later from GET /formulary/{id}. */
export function draftFromServer(m: ReviewMedicine, entry: FormularyEntry | null): Draft {
  const d = emptyDraft(m)
  const cur = m.current_decision as Partial<MedicineDecision> | null
  if (!cur || !cur.action) return d
  const se = cur.schedule_edit
  return {
    ...d,
    action: cur.action,
    formulary: entry,
    strength: cur.strength_choice ?? null,
    acks: cur.acknowledged_flags ?? [],
    note: cur.note ?? '',
    decided: true,
    schedTouched: !!se,
    sched: se ? { times: String(se.times_per_day), timing: se.timing_label, days: se.duration_days ? String(se.duration_days) : '' } : d.sched,
  }
}

/** Reasons that need an acknowledgement checkbox (name reasons are resolved by the picker, never by a tick). */
export const ackReasons = (m: ReviewMedicine) => m.reasons.filter((r) => r.kind === 'acknowledge')
export const nameReasons = (m: ReviewMedicine) => m.reasons.filter((r) => r.kind === 'name')
export const isNonDaily = (m: ReviewMedicine) => m.flags.includes('non_daily_frequency') || m.reasons.some((r) => r.id === 'non_daily_frequency')

export type Missing = 'action' | 'ack' | 'formulary' | 'strength' | 'schedule'

export function schedValid(s: SchedDraft): boolean {
  return (TIMES_CHOICES as readonly string[]).includes(s.times) && isTiming(s.timing) && (s.days === '' || (/^\d{1,3}$/.test(s.days) && +s.days >= 1 && +s.days <= 365))
}

export function missing(m: ReviewMedicine, d: Draft): Missing[] {
  if (!d.action) return ['action']
  const out: Missing[] = []
  if (d.action === 'confirm_as_extracted' || d.action === 'select_formulary_drug') {
    if (ackReasons(m).some((r) => !d.acks.includes(r.id))) out.push('ack')
    if (d.schedTouched && !schedValid(d.sched)) out.push('schedule')
  }
  if (d.action === 'select_formulary_drug') {
    if (!d.formulary) out.push('formulary')
    else if (!d.strength) out.push('strength')
  }
  return out
}

export const scheduleEdit = (s: SchedDraft): ScheduleEdit => ({ times_per_day: s.times === 'as_needed' ? 'as_needed' : Number(s.times), timing_label: s.timing as ScheduleEdit['timing_label'], duration_days: s.days ? Number(s.days) : null })

export function toDecision(m: ReviewMedicine, d: Draft): MedicineDecision | null {
  if (!d.decided || !d.action || missing(m, d).length) return null
  const base: MedicineDecision = { index: m.index, action: d.action }
  if (d.action === 'remove') return base
  if (d.action === 'not_in_list') return d.note.trim() ? { ...base, note: d.note.trim().slice(0, NOTE_MAX) } : base
  const out: MedicineDecision = { ...base, acknowledged_flags: ackReasons(m).map((r) => r.id).filter((id) => d.acks.includes(id)) }
  if (d.action === 'select_formulary_drug') {
    out.formulary_id = d.formulary!.id
    out.strength_choice = d.strength
  }
  if (d.schedTouched && !isNonDaily(m)) out.schedule_edit = scheduleEdit(d.sched)
  return out
}

export function toAdded(a: AddedDraft): AddedMedicine {
  return { formulary_id: a.formulary.id, strength_choice: a.strength, dose: a.dose as AddedMedicine['dose'], schedule: scheduleEdit(a.sched) }
}

export const addedReady = (a: Partial<AddedDraft>) => !!a.formulary && !!a.strength && !!a.dose && !!a.sched && schedValid(a.sched) && a.sched.times !== '' && a.sched.timing !== ''

/** The full set to send. Undecided medicines are simply left out (they stay unconfirmed on the server). */
export function buildConfirmations(meds: ReviewMedicine[], drafts: Record<number, Draft>, added: AddedDraft[]): Confirmations {
  const decisions = meds.flatMap((m) => {
    const x = drafts[m.index] && toDecision(m, drafts[m.index])
    return x ? [x] : []
  })
  return { decisions, added_medicines: added.map(toAdded) }
}

/** Medicines that must be confirmed and have no complete decision yet. */
export function attentionCount(meds: ReviewMedicine[], drafts: Record<number, Draft>): number {
  return meds.filter((m) => m.review_level === 'must_confirm' && !(drafts[m.index] && toDecision(m, drafts[m.index]))).length
}

/* ---- Phase 6c-5: presentation helpers (no new rules: they only read review_level, the draft and the saved summary) ---- */
export type Status = 'attention' | 'checked' | 'noaction'

/** needs your check = must_confirm with no complete decision (or the server said it is still open after a save);
 *  checked by you = a complete decision exists; no action needed = nothing flagged or notes only. */
export function statusOf(m: ReviewMedicine, d: Draft | undefined, saved?: { unresolved: string[]; review_level: string }): Status {
  if (saved && (saved.unresolved.length > 0 || saved.review_level === 'must_confirm')) return 'attention'
  if (d && toDecision(m, d)) return 'checked'
  return m.review_level === 'must_confirm' ? 'attention' : 'noaction'
}

/** Order by the API review level only (never by the person's decisions, so a card does not jump away when it is checked); ties keep document order. */
export function orderMedicines(meds: ReviewMedicine[], mode: 'attention' | 'document'): ReviewMedicine[] {
  const rank = { must_confirm: 0, note: 1, none: 2 } as const
  return [...meds].sort((a, b) => (mode === 'document' ? 0 : rank[a.review_level] - rank[b.review_level]) || a.index - b.index)
}

export type ReadParts = { strength: string | null; dose: string | null; times: number | 'as_needed' | null; timing: ScheduleEdit['timing_label'] | null; abbreviation: string | null; days: number | null; durationText: string | null }

/** What the model read, as pieces: the frequency is ONE phrase (times and timing), the abbreviation only when no number was read. */
export function readParts(m: ReviewMedicine): ReadParts {
  const f = m.frequency
  const times = typeof f.times_per_day === 'number' ? f.times_per_day : f.is_prn ? 'as_needed' : null
  return {
    strength: m.strength ?? null,
    dose: m.dose ?? null,
    times,
    timing: isTiming(f.timing_label) && f.timing_label !== 'unspecified' ? f.timing_label : null,
    abbreviation: times === null ? f.original_abbreviation ?? null : null,
    days: typeof m.duration_days === 'number' ? m.duration_days : null,
    durationText: m.duration_text ?? null,
  }
}
