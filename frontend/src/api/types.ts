/* Response types, written by hand from docs/API.md and the backend routes (openapi.json leaves response bodies untyped).
 * Request bodies come from openapi.generated.ts. Everything here is data; server text is rendered as text nodes only. */
export type Lang = 'en' | 'ta' | 'hi'
export type Health = { status: string; app: string; version: string }
export type ConsentNotice = {
  version: string
  language: Lang
  sha256: string
  title: string
  items: { id: string; text: string }[]
  purposes: { id: string; label: string; required?: boolean }[]
  review_status: string
}
export type StringsResponse = { language: Lang; strings: Record<string, string>; draft_unreviewed: boolean }

export type SessionState = {
  language: Lang
  expires_at: string
  consent: { granted: boolean; current_version: string; purposes: string[] }
  documents: number
  limits: { max_documents: number; max_upload_bytes: number }
}

export type JobState = 'queued' | 'extracting' | 'normalising' | 'awaiting_confirmation' | 'failed' | 'expired' | 'deleted'
export type NarrativeState = 'not_started' | 'pending' | 'running' | 'ready' | 'failed'
export type ErrorCode = 'ollama_unavailable' | 'image_unreadable' | 'context_truncated' | 'image_not_received' | 'timeout' | 'interrupted' | 'provider_not_allowed'
export type DocView = {
  id: string
  state: JobState
  error_code: ErrorCode | null
  error_message: string | null
  created_at: string
  updated_at: string
  image_kept: boolean
  narrative: Partial<Record<Lang, NarrativeState>>
  timings: Record<string, number>
  retry_possible: boolean
  confirmed: boolean
}

export type ReviewLevel = 'must_confirm' | 'note' | 'none'
export type Reason = { id: string; template_id: string | null; text: string | null; kind: 'name' | 'acknowledge' }
export type FormularyEntry = { id: string; generic: string; brand_names: string[]; available_strengths: string[]; form: string; route: string; strength_as_label_option: string }
export type MedicineAction = 'confirm_as_extracted' | 'select_formulary_drug' | 'not_in_list' | 'remove'
export type ReviewMedicine = {
  index: number
  ref: string
  as_written: { brand: string | null; generic: string | null }
  printed: { brand: string | null; generic: string | null }
  resolved_generic: string | null
  name_match_type: string | null
  strength: string | null
  dose: string | null
  form: string
  route: string
  frequency: { times_per_day: number | string | null; timing_label: string | null; is_prn: boolean | null; original_abbreviation: string | null }
  duration_days: number | string | null
  duration_text: string | null
  source_quote: string | null
  review_level: ReviewLevel
  flags: string[]
  reasons: Reason[]
  interaction_ready: boolean
  schedule_ready: boolean
  has_exact_identity: boolean
  allowed_actions: MedicineAction[]
  current_decision: Record<string, unknown> | null
}
export type MedicinesResponse = {
  medicines: ReviewMedicine[]
  added_medicines: Record<string, unknown>[]
  dose_options: string[]
  strength_as_label_option: string
  formulary_status: string
  compare_note: string
}
export type FormularySearch = { results: FormularyEntry[]; formulary_status: string }
export type ConfirmedSummary = { ref: string; resolution: string; interaction_ready: boolean; schedule_ready: boolean; review_level: ReviewLevel; unresolved: string[]; not_checked_reason: string | null }
export type ConfirmResponse = { confirmed: boolean; medicines: ConfirmedSummary[]; removed: unknown[] }

export type LabelKey = 'native_reviewed' | 'draft_unreviewed' | 'machine_checked' | 'original_only' | null
export type LangText = { text: string; status: string; display_mode: string; review_status: string; provenance: string; label: string | null; label_key: LabelKey }
export type ResultLine = {
  line_id: string
  source_ref: number | null
  kind: 'disclaimer' | 'medicine' | 'safety' | 'follow_up' | 'advice' | 'warning' | 'not_found'
  text: Partial<Record<Lang, LangText>>
  source_text: string
  provenance: string
  status: string
  display_mode: string
  review_level: ReviewLevel
  flags: string[]
  notices: { code: string; text: Partial<Record<Lang, LangText>> }[]
  settled: boolean
  narrative_pending: boolean
}
export type ResultSection = { id: 'disclaimer' | 'medicines' | 'safety' | 'follow_ups' | 'advice' | 'warnings' | 'not_found'; heading: Partial<Record<Lang, string>>; lines: ResultLine[] }
export type Level = 'major' | 'moderate' | 'minor' | 'unknown'
export type PairResult = {
  a: number
  b: number
  generic_a: string | null
  generic_b: string | null
  status: 'interaction_found' | 'not_checked_no_record' | 'not_checked_unconfirmed' | 'not_checked_database_missing'
  level: Level | null
  source: 'ddinter' | 'curated_reviewed' | 'curated_author_checked' | null
  same_medicine: boolean
}
export type ResultResponse = {
  document_id: string
  language: Lang
  confirmed: boolean
  confirm_first: boolean
  narrative_status: Record<Lang, NarrativeState>
  explanation: {
    document_type: string
    sections: ResultSection[]
    safety: { pair_results: PairResult[]; duplicate_notices: { indices: number[]; name: string }[]; overall_state: string; supplement_author_checked: boolean } | null
    guardrail_events: string[]
  }
  medicines_meta: { line_id: string; ref: string; resolution: string; unresolved: string[]; not_checked_reason: string | null; interaction_ready: boolean; schedule_ready: boolean; labels: { template_id: string; text: string }[] }[]
  removed: unknown[]
  guardrail_events: string[]
}

export type Slot = { med_ref: string; name: string; time: string; source: 'user' | 'suggested' }
export type ScheduleMed = { ref: string; name: string; strength: string | null; dose: string | null; times_per_day: number | string | null; timing_label: string | null; times: string[]; source: 'user' | 'suggested'; duration_days: number | null; duration_text: string | null }
export type NotScheduled = { ref: string; name: string; reason: string; template_id: string; text: string; user_can_set_times: boolean }
export type ScheduleResponse = {
  document_id: string
  language: Lang
  notice: { template_id: string; text: string }
  extra_notices: { template_id: string; text: string }[]
  slots: Slot[]
  medicines: ScheduleMed[]
  not_scheduled: NotScheduled[]
  guardrail_events: string[]
}
export type AdherenceEvent = { id: string; document_id?: string; med_ref: string; scheduled_time: string; date: string; status: 'taken' | 'skipped' }
export type DoctorSummary = {
  document_id: string
  language: Lang
  title: string
  period: { from: string; to: string }
  headings: Record<'medicines' | 'adherence' | 'unconfirmed' | 'interactions', string>
  labels: Record<'taken' | 'skipped' | 'missed', string>
  medicines: (Pick<ScheduleMed, 'ref' | 'name' | 'strength' | 'dose' | 'times_per_day' | 'timing_label' | 'times' | 'duration_days' | 'duration_text'> & { taken: number; skipped: number; missed: number })[]
  unconfirmed: { ref: string; name: string; reasons: { id: string; text: string | null }[] }[]
  not_scheduled: NotScheduled[]
  interactions: { lines: string[]; found: { a: number; b: number; generic_a: string; generic_b: string; level: string }[] }
  schedule_notice: string
  disclaimer: string
  guardrail_events: string[]
}
export type DeleteReceipt = { deleted: Record<string, number>; deleted_at: string; message: string; receipt: string }
