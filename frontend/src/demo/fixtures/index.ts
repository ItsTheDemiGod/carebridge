/* The pre-recorded responses (scripts/build_demo_data.py). One lazy chunk: only a visitor of /demo downloads it. */
import confirm_response from './confirm_response.json'
import consent_notice_en from './consent_notice_en.json'
import document from './document.json'
import documents from './documents.json'
import formulary from './formulary.json'
import session from './session.json'
import scripted_decisions from './scripted_decisions.json'
import doctor_summary_en from './doctor_summary_en.json'
import doctor_summary_ta from './doctor_summary_ta.json'
import doctor_summary_hi from './doctor_summary_hi.json'
import medicines_before_en from './medicines_before_en.json'
import medicines_before_ta from './medicines_before_ta.json'
import medicines_before_hi from './medicines_before_hi.json'
import medicines_after_en from './medicines_after_en.json'
import medicines_after_ta from './medicines_after_ta.json'
import medicines_after_hi from './medicines_after_hi.json'
import result_before_en from './result_before_en.json'
import result_before_ta from './result_before_ta.json'
import result_before_hi from './result_before_hi.json'
import result_after_en from './result_after_en.json'
import result_after_ta from './result_after_ta.json'
import result_after_hi from './result_after_hi.json'
import schedule_en from './schedule_en.json'
import schedule_ta from './schedule_ta.json'
import schedule_hi from './schedule_hi.json'
import strings_en from './strings_en.json'
import strings_ta from './strings_ta.json'
import strings_hi from './strings_hi.json'

type Lang = 'en' | 'ta' | 'hi'
// per-language recordings differ only in text; they are typed where they are used (demoApi.ts, checked against api/types in demo.test.ts)
const by = (en: unknown, ta: unknown, hi: unknown): Record<Lang, unknown> => ({ en, ta, hi })

export const fixtures = {
  session: session.data,
  document: document.data,
  documents: documents.data,
  consentNotice: consent_notice_en.data,
  confirmResponse: confirm_response.data,
  scriptedDecisions: scripted_decisions.data,
  formulary: formulary.data,
  strings: by(strings_en.data, strings_ta.data, strings_hi.data),
  medicinesBefore: by(medicines_before_en.data, medicines_before_ta.data, medicines_before_hi.data),
  medicinesAfter: by(medicines_after_en.data, medicines_after_ta.data, medicines_after_hi.data),
  resultBefore: by(result_before_en.data, result_before_ta.data, result_before_hi.data),
  resultAfter: by(result_after_en.data, result_after_ta.data, result_after_hi.data),
  schedule: by(schedule_en.data, schedule_ta.data, schedule_hi.data),
  doctorSummary: by(doctor_summary_en.data, doctor_summary_ta.data, doctor_summary_hi.data),
}
export const meta = { source_document: session && document._meta.source_document, condition: document._meta.condition, built_on: document._meta.built_on }
