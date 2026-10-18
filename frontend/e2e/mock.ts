/* A stateful fake of the CareBridge API for Playwright (network interception, deterministic). Every request body the app sends is validated
 * against the request schemas of docs/openapi.json; a body that does not match answers 422 like the real backend, so contract drift fails the tests. */
import { API } from './helpers'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { Page, Route } from '@playwright/test'
import type { AdherenceEvent, DocView, Lang } from '../src/api/types'
import { DOC_ID, NOTICE_VERSION, consentNotice, doc, medicines, result, schedule, searchFormulary, session } from './fixtures'

const SPEC = JSON.parse(readFileSync(fileURLToPath(new URL('../../docs/openapi.json', import.meta.url)), 'utf8'))

// ---- minimal JSON-schema check (the subset openapi.json uses for request bodies)
type Schema = Record<string, any> // eslint-disable-line
export function validate(schema: Schema, v: unknown, path = '$'): string[] {
  if (schema.$ref) return validate(SPEC.components.schemas[schema.$ref.split('/').pop()!], v, path)
  if (schema.anyOf) {
    const errs = schema.anyOf.map((s: Schema) => validate(s, v, path))
    return errs.some((e: string[]) => e.length === 0) ? [] : [`${path}: matches no alternative`]
  }
  if (schema.enum && !schema.enum.includes(v)) return [`${path}: not one of ${schema.enum.join(',')}`]
  if (schema.const !== undefined && v !== schema.const) return [`${path}: not ${schema.const}`]
  switch (schema.type) {
    case 'string':
      return typeof v !== 'string' ? [`${path}: not a string`] : schema.maxLength && v.length > schema.maxLength ? [`${path}: too long`] : []
    case 'integer':
      return !Number.isInteger(v) ? [`${path}: not an integer`] : schema.minimum !== undefined && (v as number) < schema.minimum ? [`${path}: below minimum`] : schema.maximum !== undefined && (v as number) > schema.maximum ? [`${path}: above maximum`] : []
    case 'null':
      return v === null ? [] : [`${path}: not null`]
    case 'array':
      if (!Array.isArray(v)) return [`${path}: not an array`]
      if (schema.maxItems && v.length > schema.maxItems) return [`${path}: too many items`]
      return v.flatMap((x, i) => validate(schema.items ?? {}, x, `${path}[${i}]`))
    case 'object': {
      if (typeof v !== 'object' || v === null || Array.isArray(v)) return [`${path}: not an object`]
      const o = v as Record<string, unknown>
      const props: Record<string, Schema> = schema.properties ?? {}
      const errs: string[] = []
      for (const r of schema.required ?? []) if (!(r in o)) errs.push(`${path}.${r}: required`)
      for (const [k, x] of Object.entries(o)) {
        if (props[k]) errs.push(...validate(props[k], x, `${path}.${k}`))
        else if (schema.additionalProperties === false) errs.push(`${path}.${k}: unexpected field`)
        else if (schema.additionalProperties && typeof schema.additionalProperties === 'object') errs.push(...validate(schema.additionalProperties, x, `${path}.${k}`))
      }
      return errs
    }
    default:
      return []
  }
}

const bodySchema = (method: string, specPath: string): Schema | undefined => SPEC.paths[specPath]?.[method.toLowerCase()]?.requestBody?.content?.['application/json']?.schema

export type Call = { method: string; path: string; body: unknown; origin: string }
export type Fail = { status: number; code: string; message?: string; headers?: Record<string, string>; times?: number }
export type MockOptions = {
  lang?: Lang
  /** a session cookie already exists (GET /session answers 200) */
  hasSession?: boolean
  consented?: boolean
  /** job states returned by successive GETs of the document (the last one repeats) */
  docSteps?: DocView['state'][]
  errorCode?: DocView['error_code']
  imageKept?: boolean
  /** bytes served by GET /documents/{id}/image (default: a 1 px PNG); used for realistic screenshots */
  imageBody?: Buffer
  /** failures keyed by "METHOD /api/v1/path-with-{id}" */
  fail?: Record<string, Fail>
  /** GETs of /result before a running narrative becomes ready */
  narrativeAfter?: number
  narrativeFinal?: 'ready' | 'failed'
  /** start with a document already waiting for confirmation */
  docReady?: boolean
}

export type Mock = {
  calls: Call[]
  s: {
    session: ReturnType<typeof session> | null
    docs: DocView[]
    confirmations: { decisions?: { index: number; action: string; [k: string]: unknown }[]; added_medicines?: unknown[] } | null
    events: AdherenceEvent[]
    overrides: Record<string, string[]>
    narrative: Record<Lang, 'not_started' | 'pending' | 'running' | 'ready' | 'failed'>
    noticeVersion: string
    deleted: boolean
  }
  expire: () => void
  setNoticeVersion: (v: string) => void
  count: (m: string, p: RegExp | string) => number
}

export async function mockApi(page: Page, o: MockOptions = {}): Promise<Mock> {
  const lang0 = o.lang ?? 'en'
  const mock: Mock = {
    calls: [],
    s: {
      session: o.hasSession || o.consented ? session({ consent: { granted: !!o.consented, current_version: NOTICE_VERSION, purposes: o.consented ? ['process_photo', 'store_results_for_session'] : [] }, documents: o.docReady ? 1 : 0 }, lang0) : null,
      docs: o.docReady ? [doc({ state: 'awaiting_confirmation', image_kept: !!o.imageKept, narrative: { en: 'running' } })] : [],
      confirmations: null, events: [], overrides: {}, narrative: { en: 'ready', ta: 'not_started', hi: 'not_started' }, noticeVersion: NOTICE_VERSION, deleted: false,
    },
    expire() { this.s.session = null },
    setNoticeVersion(v) { this.s.noticeVersion = v },
    count(m, p) { return this.calls.filter((c) => c.method === m && (typeof p === 'string' ? c.path.startsWith(p) : p.test(c.path))).length },
  }
  const steps = o.docSteps ?? ['queued', 'extracting', 'normalising', 'awaiting_confirmation']
  let step = 0
  const resultGets: Partial<Record<Lang, number>> = {}
  const failCounts: Record<string, number> = {}
  const json = (r: Route, status: number, body: unknown, headers: Record<string, string> = {}) => r.fulfill({ status, contentType: 'application/json', headers, body: JSON.stringify(body) })
  const err = (r: Route, status: number, code: string, message?: string, headers?: Record<string, string>) => json(r, status, { error: { code, message: message ?? `error.${code}` } }, headers)
  const view = (d: DocView): DocView => ({ ...d, narrative: d.state === 'awaiting_confirmation' ? { en: mock.s.narrative.en, ...(mock.s.narrative.ta !== 'not_started' ? { ta: mock.s.narrative.ta } : {}), ...(mock.s.narrative.hi !== 'not_started' ? { hi: mock.s.narrative.hi } : {}) } : d.narrative, confirmed: !!mock.s.confirmations })
  const setDoc = (d: DocView) => (mock.s.docs = [d])

  await page.route(API, async (route) => {
    const req = route.request()
    const url = new URL(req.url())
    const path = url.pathname
    const method = req.method()
    if (method === 'OPTIONS') return route.fulfill({ status: 204 })
    let body: unknown = null
    const ct = req.headers()['content-type'] ?? ''
    if (ct.includes('json')) {
      try { body = req.postDataJSON() } catch { body = null }
    } else if (req.postDataBuffer()) body = { bytes: req.postDataBuffer()!.length, type: ct }
    mock.calls.push({ method, path: path + url.search, body, origin: req.headers()['origin'] ?? '' })

    // generic path key for failure injection and spec validation
    const key = `${method} ${path.replace(DOC_ID, '{doc_id}').replace(/\/adherence\/[^/]+$/, '/adherence/{event_id}').replace(/\/formulary\/(?!search)[^/]+$/, '/formulary/{fid}')}`
    const f = o.fail?.[key]
    if (f && (failCounts[key] = (failCounts[key] ?? 0) + 1) <= (f.times ?? Infinity)) return err(route, f.status, f.code, f.message, f.headers)
    if (method !== 'GET' && method !== 'HEAD' && req.headers()['x-carebridge-request'] !== '1') return err(route, 403, 'request_blocked')
    const schema = bodySchema(method, key.split(' ')[1])
    if (schema && body !== null) {
      const errs = validate(schema, body)
      if (errs.length) return err(route, 422, 'invalid_request', errs.join('; '))
    }

    if (path === '/api/health') return json(route, 200, { status: 'ok', app: 'CareBridge', version: 'test' })
    if (path === '/api/v1/consent-notice') return json(route, 200, consentNotice((url.searchParams.get('lang') as Lang) ?? 'en', mock.s.noticeVersion))
    if (path === '/api/v1/strings') return json(route, 200, { language: url.searchParams.get('lang') ?? 'en', strings: stringsFor(url.searchParams.get('lang') ?? 'en'), draft_unreviewed: false })
    if (path === '/api/v1/sessions' && method === 'POST') {
      const lang = (body as { language: Lang }).language
      const had = !!mock.s.session
      mock.s.session = mock.s.session ? { ...mock.s.session, language: lang } : session({}, lang)
      return json(route, had ? 200 : 201, mock.s.session)
    }
    if (path === '/api/v1/session' && method === 'DELETE') {
      if (!mock.s.session) return route.fulfill({ status: 204 })
      const n = mock.s.docs.length
      mock.s.session = null
      mock.s.docs = []
      mock.s.confirmations = null
      mock.s.events = []
      mock.s.deleted = true
      return json(route, 200, { deleted: { consents: 1, documents: n, adherence_events: 0, payloads: 2, images: 0, sessions: 1 }, deleted_at: '2026-10-17T10:00:00+00:00', message: 'Your data has been deleted and your consent is withdrawn.', receipt: `Deleted: ${n} documents, 2 saved results, 0 photos.` })
    }
    const sess = mock.s.session
    if (path.startsWith('/api/v1/') && !path.endsWith('/consent-notice') && !sess) return err(route, 401, 'session_expired')
    if (!sess) return err(route, 401, 'no_session')
    if (path === '/api/v1/session') return json(route, 200, { ...sess, documents: mock.s.docs.length })
    if (path === '/api/v1/consent' && method === 'POST') {
      const b = body as { notice_version: string; purposes: string[] }
      if (b.notice_version !== mock.s.noticeVersion || !b.purposes.includes('process_photo') || !b.purposes.includes('store_results_for_session')) return err(route, 400, 'consent_invalid')
      mock.s.session = { ...sess, consent: { granted: true, current_version: mock.s.noticeVersion, purposes: b.purposes } }
      return json(route, 200, mock.s.session)
    }
    if (path.startsWith('/api/v1/formulary/search')) return json(route, 200, { results: searchFormulary(url.searchParams.get('q') ?? ''), formulary_status: 'unverified_requires_pharmacist_review' })
    if (path.startsWith('/api/v1/formulary/')) {
      const e = searchFormulary(decodeURIComponent(path.split('/').pop()!)).find(Boolean) ?? null
      return e ? json(route, 200, { ...e, formulary_status: 'x' }) : err(route, 404, 'not_found')
    }
    if (!sess.consent.granted) return err(route, 403, 'consent_required')

    if (path === '/api/v1/documents' && method === 'POST') {
      if (mock.s.docs.length >= 10) return err(route, 429, 'too_many_documents')
      step = 0
      const d = doc({ state: 'queued', image_kept: sess.consent.purposes.includes('keep_photo_for_session') })
      setDoc(d)
      return json(route, 202, d)
    }
    if (path === '/api/v1/documents') return json(route, 200, { documents: mock.s.docs.map(view) })
    if (path === '/api/v1/adherence' && method === 'POST') {
      const b = body as AdherenceEvent & { document_id: string }
      const slots = schedule().slots
      if (!slots.some((s) => s.med_ref === b.med_ref && s.time === b.scheduled_time)) return err(route, 422, 'invalid_request')
      const ev = { id: `ev${mock.s.events.length + 1}x`, ...b }
      mock.s.events.push(ev)
      return json(route, 201, ev)
    }
    if (path === '/api/v1/adherence') return json(route, 200, { events: mock.s.events })
    const ad = path.match(/^\/api\/v1\/adherence\/([^/]+)$/)
    if (ad && method === 'DELETE') {
      const n = mock.s.events.length
      mock.s.events = mock.s.events.filter((e) => e.id !== ad[1])
      return mock.s.events.length === n ? err(route, 404, 'not_found') : route.fulfill({ status: 204 })
    }

    const m = path.match(/^\/api\/v1\/documents\/([^/]+)(?:\/([a-z-]+))?$/)
    if (!m) return err(route, 404, 'not_found')
    const d = mock.s.docs.find((x) => x.id === m[1])
    if (!d) return err(route, 404, 'not_found')
    const sub = m[2]
    if (!sub) {
      if (d.state !== 'awaiting_confirmation' && d.state !== 'failed') {
        const next = steps[Math.min(step++, steps.length - 1)]
        setDoc({ ...d, state: next, error_code: next === 'failed' ? (o.errorCode ?? 'timeout') : null, error_message: next === 'failed' ? stringsFor(sess.language)[`job.failed.${o.errorCode ?? 'timeout'}`] : null, retry_possible: next === 'failed' && d.image_kept })
      }
      return json(route, 200, view(mock.s.docs[0]))
    }
    if (sub === 'image') return d.image_kept ? route.fulfill({ status: 200, contentType: 'image/png', body: o.imageBody ?? PNG_1PX }) : err(route, 404, 'not_found')
    if (sub === 'retry') {
      if (!d.image_kept) return err(route, 409, 'retry_unavailable')
      step = 0
      setDoc({ ...d, state: 'queued', error_code: null, error_message: null, retry_possible: false })
      return json(route, 202, mock.s.docs[0])
    }
    if (d.state !== 'awaiting_confirmation') return err(route, 409, 'not_ready')
    if (sub === 'languages') {
      const l = (body as { language: Lang }).language
      if (mock.s.narrative[l] === 'not_started') mock.s.narrative[l] = 'running'
      return json(route, 202, view(d))
    }
    if (sub === 'medicines') {
      const base = medicines()
      const dec = mock.s.confirmations?.decisions ?? []
      base.medicines.forEach((x) => (x.current_decision = (dec.find((y) => y.index === x.index) as never) ?? null))
      base.added_medicines = (mock.s.confirmations?.added_medicines as never) ?? []
      return json(route, 200, base)
    }
    if (sub === 'confirmations') {
      const b = body as NonNullable<Mock['s']['confirmations']>
      const bad = (b.decisions ?? []).find((x) => x.action === 'select_formulary_drug' && !x.formulary_id)
      if (bad) return err(route, 422, 'invalid_confirmation')
      mock.s.confirmations = b
      const sum = (b.decisions ?? []).map((x) => ({ ref: `m${x.index}`, resolution: x.action === 'select_formulary_drug' ? 'selected' : 'confirmed', interaction_ready: x.action === 'select_formulary_drug' || x.index === 0, schedule_ready: x.action !== 'remove' && x.action !== 'not_in_list' && x.index !== 2, review_level: 'none', unresolved: [], not_checked_reason: x.action === 'not_in_list' ? 'user_not_in_list' : null }))
      return json(route, 200, { confirmed: true, medicines: [...sum, ...(b.added_medicines ?? []).map((_, k) => ({ ref: `a${k}`, resolution: 'added', interaction_ready: true, schedule_ready: true, review_level: 'none', unresolved: [], not_checked_reason: null }))], removed: [] })
    }
    if (sub === 'result') {
      const l = (url.searchParams.get('lang') as Lang) ?? 'en'
      resultGets[l] = (resultGets[l] ?? 0) + 1
      if (mock.s.narrative[l] === 'running' && resultGets[l]! > (o.narrativeAfter ?? 2)) mock.s.narrative[l] = o.narrativeFinal ?? 'ready'
      const confirmed = !!mock.s.confirmations
      const st = mock.s.narrative[l]
      return json(route, 200, result(l, { confirmed, narrative: { ...mock.s.narrative }, pending: st === 'running' || st === 'pending', fallback: st === 'failed', withInteraction: confirmed }))
    }
    if (sub === 'schedule') return json(route, 200, withOverrides(schedule(sess.language), mock.s.overrides))
    if (sub === 'schedule-overrides') {
      mock.s.overrides = (body as { overrides: Record<string, string[]> }).overrides
      if (Object.values(mock.s.overrides).some((t) => t.length > 6 || t.some((x) => !/^([01]\d|2[0-3]):[0-5]\d$/.test(x)))) return err(route, 422, 'invalid_request')
      return json(route, 200, withOverrides(schedule(sess.language), mock.s.overrides))
    }
    if (sub === 'doctor-summary') {
      const s = schedule(sess.language)
      const meds = s.medicines.map((x) => ({ ref: x.ref, name: x.name, strength: x.strength, dose: x.dose, times_per_day: x.times_per_day, timing_label: x.timing_label, times: x.times, duration_days: x.duration_days, duration_text: x.duration_text, taken: mock.s.events.filter((e) => e.med_ref === x.ref && e.status === 'taken').length, skipped: mock.s.events.filter((e) => e.med_ref === x.ref && e.status === 'skipped').length, missed: 1 }))
      const today = new Date().toISOString().slice(0, 10)
      return json(route, 200, {
        document_id: DOC_ID, language: sess.language, title: 'Summary to show your doctor', period: { from: url.searchParams.get('from') ?? today, to: url.searchParams.get('to') ?? today },
        headings: { medicines: 'Medicines', adherence: 'Taken, skipped and missed', unconfirmed: 'Not confirmed yet', interactions: 'Interactions found' }, labels: { taken: 'Taken', skipped: 'Skipped', missed: 'Missed' },
        medicines: meds, unconfirmed: mock.s.confirmations ? [] : [{ ref: 'm1', name: 'Netfornin', reasons: [{ id: 'unresolved_name', text: 'The name could not be found in our list.' }] }], not_scheduled: s.not_scheduled,
        interactions: { lines: mock.s.confirmations ? ['Glycomet and Pantop: a possible interaction was found. Please talk to your doctor or pharmacist.'] : [], found: mock.s.confirmations ? [{ a: 0, b: 3, generic_a: 'Metformin', generic_b: 'Pantoprazole', level: 'moderate' }] : [] },
        schedule_notice: s.notice.text, disclaimer: 'This summary lists what was read from your document and what you entered. It may contain mistakes. It is not medical advice.', guardrail_events: [],
      })
    }
    return err(route, 404, 'not_found')
  })
  return mock
}

function withOverrides(s: ReturnType<typeof schedule>, over: Record<string, string[]>) {
  const medicines = s.medicines.map((m) => (over[m.ref] ? { ...m, times: [...over[m.ref]].sort(), source: 'user' as const } : m))
  const slots = medicines.flatMap((m) => m.times.map((t) => ({ med_ref: m.ref, name: m.name, time: t, source: m.source }))).sort((a, b) => a.time.localeCompare(b.time))
  return { ...s, medicines, slots }
}

const PNG_1PX = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==', 'base64')

/** the backend-owned strings exactly as the real GET /strings serves them (same prefixes, same templates file) */
const PREFIXES = ['error.', 'job.', 'status.', 'confirm.', 'picker.', 'schedule.', 'summary.', 'consent.', 'delete.', 'label.', 'heading.', 'timing.', 'banner.', 'notice.']
const TEMPLATES = JSON.parse(readFileSync(fileURLToPath(new URL('../../data/templates/templates.json', import.meta.url)), 'utf8')).strings as Record<string, Record<string, { text: string }>>
const stringsFor = (lang: string) => Object.fromEntries(Object.entries(TEMPLATES).filter(([k]) => PREFIXES.some((p) => k.startsWith(p))).map(([k, v]) => [k, (v[lang] ?? v.en).text]))
