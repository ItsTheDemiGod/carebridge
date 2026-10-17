/* Typed fixtures shaped like the API contract (src/api/types.ts, requests from docs/openapi.json). Synthetic data only. */
import type {
  DocView, FormularyEntry, Lang, MedicinesResponse, ResultLine, ResultResponse, ReviewMedicine, ScheduleResponse, SessionState,
} from '../src/api/types'

export const NOTICE_VERSION = '2'
export const DOC_ID = 'Vm6VdocTESTdoc0001'

export const session = (over: Partial<SessionState> = {}, lang: Lang = 'en'): SessionState => ({
  language: lang,
  expires_at: '2099-01-01T00:00:00+00:00',
  consent: { granted: false, current_version: NOTICE_VERSION, purposes: [] },
  documents: 0,
  limits: { max_documents: 10, max_upload_bytes: 10_000_000 },
  ...over,
})

export const doc = (over: Partial<DocView> = {}): DocView => ({
  id: DOC_ID, state: 'queued', error_code: null, error_message: null, created_at: '2026-10-17T10:00:00+00:00', updated_at: '2026-10-17T10:00:00+00:00',
  image_kept: false, narrative: {}, timings: {}, retry_possible: false, confirmed: false, ...over,
})

export const consentNotice = (lang: Lang = 'en', version = NOTICE_VERSION) => ({
  version, language: lang, sha256: 'x'.repeat(64), title: lang === 'en' ? 'Before we start' : 'Before we start (draft)', review_status: 'not_required',
  items: ['what', 'where', 'stored', 'how_long', 'delete', 'no_sharing', 'prototype', 'translation_draft', 'interaction_limited', 'contact'].map((id) => ({ id, text: `Notice item ${id}.` })),
  purposes: [
    { id: 'process_photo', label: 'Read the photo of my document (required)', required: true, default: true },
    { id: 'store_results_for_session', label: 'Save the results for this session (required)', required: true, default: true },
    { id: 'keep_photo_for_session', label: 'Also keep the photo for this session (optional)', required: false, default: false },
  ],
})

const ACTIONS: ReviewMedicine['allowed_actions'] = ['confirm_as_extracted', 'select_formulary_drug', 'not_in_list', 'remove']
const base = (i: number): ReviewMedicine => ({
  index: i, ref: `m${i}`, as_written: { brand: null, generic: null }, printed: { brand: null, generic: null }, resolved_generic: null, name_match_type: null,
  strength: null, dose: '1 tablet', form: 'tablet', route: 'oral', frequency: { times_per_day: 2, timing_label: 'after_meals', is_prn: false, original_abbreviation: 'BD PC' },
  duration_days: 5, duration_text: '5 days', source_quote: null, review_level: 'none', flags: [], reasons: [], interaction_ready: true, schedule_ready: true, has_exact_identity: true,
  allowed_actions: ACTIONS, current_decision: null,
})

export const REASON = {
  unresolved_name: { id: 'unresolved_name', template_id: 'confirm.flag.unresolved_name', text: 'The name could not be found in our list. Choose the right medicine from the list, or say it is not in the list.', kind: 'name' as const },
  unusual_strength: { id: 'unusual_strength', template_id: 'confirm.flag.unusual_strength', text: 'This strength is not one of the usual strengths for this medicine. I have checked it on my label.', kind: 'acknowledge' as const },
  non_daily: { id: 'non_daily_frequency', template_id: 'confirm.flag.non_daily_frequency', text: 'This medicine does not seem to be taken every day. I have checked how often with my document.', kind: 'acknowledge' as const },
}

/** m0 clean, m1 garbled name + unusual strength, m2 weekly (non-daily), m3 note level with a short-form duration */
export const medicines = (): MedicinesResponse => ({
  medicines: [
    { ...base(0), as_written: { brand: 'Glycomet', generic: null }, printed: { brand: 'Glycomet', generic: 'Metformin' }, resolved_generic: 'Metformin', name_match_type: 'exact', strength: '500 mg', source_quote: 'Tab Glycomet 500 mg BD PC x 5 days' },
    { ...base(1), as_written: { brand: 'Netfornin', generic: null }, strength: '500 mg', review_level: 'must_confirm', flags: ['unresolved_name', 'unusual_strength'], reasons: [REASON.unresolved_name, REASON.unusual_strength], interaction_ready: false, schedule_ready: false, has_exact_identity: false, source_quote: 'Tab Netfornin 500 mg BD PC x 5 days' },
    { ...base(2), as_written: { brand: 'Alendronate', generic: null }, printed: { brand: null, generic: 'Alendronate' }, resolved_generic: 'Alendronate', name_match_type: 'exact', strength: '70 mg', review_level: 'must_confirm', flags: ['non_daily_frequency'], reasons: [REASON.non_daily], frequency: { times_per_day: 1, timing_label: 'morning', is_prn: false, original_abbreviation: 'weekly' }, schedule_ready: false, source_quote: 'Alendronate 70 mg once weekly in the morning' },
    { ...base(3), as_written: { brand: 'Pantop', generic: null }, printed: { brand: 'Pantop', generic: 'Pantoprazole' }, resolved_generic: 'Pantoprazole', name_match_type: 'exact', strength: '40 mg', review_level: 'note', source_quote: 'Tab Pantop 40 mg OD before breakfast', frequency: { times_per_day: 1, timing_label: 'before_meals', is_prn: false, original_abbreviation: 'OD' } },
  ],
  added_medicines: [],
  dose_options: ['1/2 tablet', '1 tablet', '2 tablets', '1 capsule', '2 capsules', '5 ml', '10 ml', '1 puff', '2 puffs', '1 drop', '2 drops', '1 application'],
  strength_as_label_option: 'as_on_my_label',
  formulary_status: 'unverified_requires_pharmacist_review',
  compare_note: 'Compare the brand name, generic name and strength with your document before you choose.',
})

export const FORMULARY: FormularyEntry[] = [
  { id: 'metformin', generic: 'Metformin', brand_names: ['Glycomet', 'Glucophage'], available_strengths: ['500 mg', '850 mg', '1000 mg'], form: 'tablet', route: 'oral', strength_as_label_option: 'as_on_my_label' },
  { id: 'pantoprazole', generic: 'Pantoprazole', brand_names: ['Pantop', 'Pan'], available_strengths: ['20 mg', '40 mg'], form: 'tablet', route: 'oral', strength_as_label_option: 'as_on_my_label' },
  { id: 'omeprazole', generic: 'Omeprazole', brand_names: ['Omez'], available_strengths: ['20 mg'], form: 'capsule', route: 'oral', strength_as_label_option: 'as_on_my_label' },
  { id: 'amlodipine', generic: 'Amlodipine', brand_names: ['Amlong', 'Norvasc'], available_strengths: ['2.5 mg', '5 mg', '10 mg'], form: 'tablet', route: 'oral', strength_as_label_option: 'as_on_my_label' },
]

export const searchFormulary = (q: string) => FORMULARY.filter((f) => `${f.generic} ${f.brand_names.join(' ')}`.toLowerCase().includes(q.toLowerCase())).slice(0, 20)

const lt = (text: string, over: Record<string, unknown> = {}) => ({ text, status: 'template', display_mode: 'explanation', review_status: 'not_required', provenance: 'template', label: null, label_key: null, ...over })
export const line = (id: string, kind: ResultLine['kind'], lang: Lang, text: string, over: Partial<ResultLine> & { prov?: string; label_key?: string | null; label?: string | null } = {}): ResultLine => {
  const { prov = 'template', label_key = null, label = null, ...rest } = over
  const review_status = lang === 'en' ? 'not_required' : 'draft_unreviewed'
  return {
    line_id: id, source_ref: null, kind, text: { [lang]: lt(text, { provenance: prov, label_key, label, review_status }) } as ResultLine['text'], source_text: text, provenance: prov, status: 'template', display_mode: 'explanation',
    review_level: 'none', flags: [], notices: [], settled: false, narrative_pending: false, ...rest,
  } as ResultLine
}

export type ResultOpts = { confirmed: boolean; narrative: Record<Lang, 'not_started' | 'pending' | 'running' | 'ready' | 'failed'>; pending?: boolean; fallback?: boolean; withInteraction?: boolean }
export function result(lang: Lang, o: ResultOpts): ResultResponse {
  const pending = !!o.pending
  const adv = pending
    ? line('advice-0', 'advice', lang, 'Still preparing this explanation. Please check again in a moment.', { narrative_pending: true })
    : o.fallback
      ? line('advice-0', 'advice', lang, 'Drink plenty of water.', { prov: 'original_only', label_key: 'original_only', notices: [{ code: 'fallback', text: { [lang]: lt('This explanation could not be checked in your language, so the original text from your document is shown.') } as never }] })
      : line('advice-0', 'advice', lang, lang === 'en' ? 'Drink plenty of water.' : 'நிறைய தண்ணீர் குடியுங்கள்.', { prov: lang === 'en' ? 'phrase_library' : 'model_checked', label_key: lang === 'en' ? null : 'machine_checked' })
  const medLine = (i: number, text: string, level: 'none' | 'must_confirm', settled: boolean) =>
    line(`med-${i}`, 'medicine', lang, text, { review_level: level, settled, label_key: lang === 'en' ? null : 'draft_unreviewed', notices: level === 'must_confirm' ? [{ code: 'must_confirm', text: { [lang]: lt('Please check this medicine against your document or label before using it.') } as never }] : [] })
  const found = !!o.withInteraction
  return {
    document_id: DOC_ID, language: lang, confirmed: o.confirmed, confirm_first: !o.confirmed, narrative_status: o.narrative,
    explanation: {
      document_type: 'discharge_summary',
      sections: [
        { id: 'medicines', heading: { [lang]: 'Your medicines' }, lines: [medLine(0, 'Glycomet 500 mg: take 1 tablet twice a day, after meals, for 5 days.', 'none', true), medLine(1, 'Netfornin 500 mg: take 1 tablet twice a day, after meals.', o.confirmed ? 'none' : 'must_confirm', o.confirmed)] },
        { id: 'safety', heading: { [lang]: 'Medicine interactions' }, lines: [
          ...(o.confirmed ? [] : [line('safety-banner', 'safety', lang, 'Some medicine details need your confirmation first, so the interaction results below may be incomplete. Please confirm them.')]),
          ...(found ? [line('safety-pair-0', 'safety', lang, 'Glycomet and Pantop: a possible interaction was found. Please talk to your doctor or pharmacist.')] : []),
          line('safety-not-checked', 'safety', lang, 'We could not check 5 pairs of your medicines. This does not mean they are safe.'),
          line('safety-brand-notice', 'safety', lang, 'Brand names were matched to generic names using a list that has not been checked by a pharmacist.'),
          line('safety-attribution', 'safety', lang, 'Interaction information comes from DDInter.'),
        ] },
        { id: 'advice', heading: { [lang]: 'Diet and activity' }, lines: [adv] },
        { id: 'warnings', heading: { [lang]: 'Warning signs' }, lines: [line('warning-0', 'warning', lang, 'Seek urgent care if you have chest pain.', { prov: 'phrase_library', label_key: lang === 'en' ? null : 'draft_unreviewed' })] },
      ],
      safety: {
        pair_results: found ? [{ a: 0, b: 3, generic_a: 'Metformin', generic_b: 'Pantoprazole', status: 'interaction_found', level: 'moderate', source: 'ddinter', same_medicine: false }] : [],
        duplicate_notices: [], overall_state: o.confirmed ? (found ? 'review_interactions' : 'ok_to_review') : 'confirm_first', supplement_author_checked: true,
      },
      guardrail_events: [],
    },
    medicines_meta: [
      { line_id: 'med-0', ref: 'm0', resolution: 'extracted', unresolved: [], not_checked_reason: null, interaction_ready: true, schedule_ready: true, labels: [] },
      { line_id: 'med-1', ref: 'm1', resolution: o.confirmed ? 'selected' : 'extracted', unresolved: o.confirmed ? [] : ['unresolved_name'], not_checked_reason: null, interaction_ready: o.confirmed, schedule_ready: o.confirmed, labels: o.confirmed ? [{ template_id: 'confirm.you_selected', text: 'You chose this medicine from the list.' }] : [] },
    ],
    removed: [], guardrail_events: [],
  }
}

export const schedule = (lang: Lang = 'en'): ScheduleResponse => ({
  document_id: DOC_ID, language: lang, notice: { template_id: 'schedule.notice', text: "Suggested times only; adjust them to match your doctor's instructions." }, extra_notices: [],
  slots: [
    { med_ref: 'm0', name: 'Glycomet', time: '08:30', source: 'suggested' }, { med_ref: 'm0', name: 'Glycomet', time: '20:30', source: 'suggested' },
    { med_ref: 'm3', name: 'Pantop', time: '07:30', source: 'suggested' },
  ],
  medicines: [
    { ref: 'm0', name: 'Glycomet', strength: '500 mg', dose: '1 tablet', times_per_day: 2, timing_label: 'after_meals', times: ['08:30', '20:30'], source: 'suggested', duration_days: 5, duration_text: 'About 5 days in total.' },
    { ref: 'm3', name: 'Pantop', strength: '40 mg', dose: '1 tablet', times_per_day: 1, timing_label: 'before_meals', times: ['07:30'], source: 'suggested', duration_days: null, duration_text: null },
  ],
  not_scheduled: [{ ref: 'm2', name: 'Alendronate', reason: 'non_daily', template_id: 'schedule.not.non_daily', text: 'Not scheduled: this medicine is not taken every day. Follow your document.', user_can_set_times: false }],
  guardrail_events: [],
})
