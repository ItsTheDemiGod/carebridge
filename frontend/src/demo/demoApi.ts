/* DemoApi: answers the typed client's calls under /demo from the committed pre-recorded fixtures, held in memory.
 * No fetch to /api, no session, no consent call, nothing stored (not even in localStorage); the state below is dropped when the person leaves
 * the sample (resetDemo). Only static app files are fetched: the fixture chunk and the sample photo under /demo/. Resolves immediately: no simulated waiting. */
import { ApiError } from '../api/apiError'
import type { Options } from '../api/client'
import type { Lang } from '../api/types'
import { stripBase, withBase } from '../lib/mode'

export const DEMO_ID = 'demo'
export const DEMO_IMAGE = withBase('demo/sample-document.png')
export const isDemoPath = (raw: string) => {
  const p = stripBase(raw)
  return p === '/demo' || p.startsWith('/demo/')
}

type Fixtures = typeof import('./fixtures').fixtures
type Json = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
type Event = { id: string; document_id: string; med_ref: string; scheduled_time: string; date: string; status: 'taken' | 'skipped' }

const fresh = () => ({ lang: 'en' as Lang, confirmed: false, events: [] as Event[], overrides: {} as Record<string, string[]>, seq: 0 })
let st = fresh()
let fx: Fixtures | null = null
let image: Blob | null = null

/** Forget everything the person did in the sample (called when they leave /demo). */
export const resetDemo = () => {
  st = fresh()
}
export const demoState = () => ({ confirmed: st.confirmed })

/** Fixtures (one lazy chunk) and the sample photo; the intro page calls this so the rest of the sample works without any network. */
let loading: Promise<void> | null = null
export function preloadDemo(): Promise<void> {
  loading ??= (async () => {
    fx = (await import('./fixtures')).fixtures
    image = await (await fetch(DEMO_IMAGE)).blob()
  })().catch((e) => {
    loading = null // a failed load (offline before the first visit) can be tried again
    throw e
  })
  return loading
}

const clone = <T,>(x: T): T => structuredClone(x)
const bad = (status: number, code: string) => new ApiError(status, code, '')
const today = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const asLang = (l: string | null): Lang => (l === 'ta' || l === 'hi' ? l : 'en')

/** The recorded picker searches cover the typed prefixes; any other text is matched the same simple way (substring of the generic or a brand name) over the recorded entries only. */
function searchRecorded(f: Fixtures, text: string, limit: number) {
  const q = text.trim().toLowerCase()
  const entries = Object.values(f.formulary.entries) as Json[]
  const hit = q ? entries.filter((e) => [e.generic, ...(e.brand_names ?? [])].some((n: string) => n.toLowerCase().includes(q))) : []
  return { results: hit.slice(0, limit).map(({ formulary_status: _s, ...e }) => e), formulary_status: f.formulary.formulary_status }
}

function scheduleView(f: Fixtures): Json {
  const s = clone(f.schedule[st.lang]) as Json
  for (const m of s.medicines as Json[]) if (st.overrides[m.ref]) Object.assign(m, { times: [...st.overrides[m.ref]], source: 'user' })
  s.slots = (s.medicines as Json[]).flatMap((m) => (m.times as string[]).map((time) => ({ med_ref: m.ref, name: m.name, time, source: m.source }))).sort((a, b) => a.time.localeCompare(b.time))
  return s
}

function summaryView(f: Fixtures): Json {
  const s = clone(f.doctorSummary[st.lang]) as Json
  s.period = { from: today(), to: today() }
  for (const m of s.medicines as Json[]) {
    const ev = st.events.filter((e) => e.med_ref === m.ref)
    const taken = ev.filter((e) => e.status === 'taken').length
    const skipped = ev.filter((e) => e.status === 'skipped').length
    Object.assign(m, { taken, skipped, missed: Math.max(0, (m.times as string[]).length - taken - skipped) })
  }
  return s
}

export async function demoApi<T>(path: string, opts: Options = {}): Promise<T> {
  await preloadDemo().catch(() => {
    throw bad(0, 'network_error')
  })
  const f = fx!
  const method = (opts.method ?? 'GET').toUpperCase()
  const [p, qs = ''] = path.replace(/^\/api\/v1/, '').split('?')
  const q = new URLSearchParams(qs)
  const body = (opts.body ?? {}) as Json
  const out = (x: unknown) => x as T
  const session = () => ({ ...clone(f.session), language: st.lang, documents: 1 })
  const doc = () => ({ ...clone(f.document), image_kept: true, confirmed: st.confirmed })

  if (p === '/strings') {
    const all = f.strings[asLang(q.get('lang'))] as Json
    const prefix = q.get('prefix') ?? ''
    return out(prefix ? { ...all, strings: Object.fromEntries(Object.entries(all.strings as Json).filter(([k]) => k.startsWith(prefix))) } : clone(all))
  }
  if (p === '/consent-notice') return out(clone(f.consentNotice))
  if (p === '/sessions' && method === 'POST') {
    st.lang = asLang(body.language)
    return out(session())
  }
  if (p === '/session' && method === 'GET') return out(session())
  if (p === '/consent' && method === 'POST') return out(session())
  if (p === '/documents' && method === 'GET') return out({ documents: [doc()] })
  if (p === `/documents/${DEMO_ID}` && method === 'GET') return out(doc())
  if (p === `/documents/${DEMO_ID}/languages` && method === 'POST') return out(doc())
  if (p === `/documents/${DEMO_ID}/image`) {
    if (!image) throw bad(404, 'not_found')
    return out(image)
  }
  if (p === `/documents/${DEMO_ID}/medicines`) return out(clone((st.confirmed ? f.medicinesAfter : f.medicinesBefore)[st.lang]))
  if (p === `/documents/${DEMO_ID}/confirmations` && method === 'POST') {
    if (!Array.isArray(body.decisions)) throw bad(422, 'invalid_request')
    st.confirmed = true // the pre-recorded AFTER state, whatever was chosen (the page says so)
    return out(clone(f.confirmResponse))
  }
  if (p === '/formulary/search') return out(searchRecorded(f, q.get('q') ?? '', Math.min(20, Number(q.get('limit') ?? 20))))
  const fe = p.match(/^\/formulary\/(.+)$/)
  if (fe) {
    const e = (f.formulary.entries as Json)[decodeURIComponent(fe[1])]
    if (!e) throw bad(404, 'not_found')
    return out(clone(e))
  }
  if (p === `/documents/${DEMO_ID}/result`) {
    const lang = asLang(q.get('lang') ?? st.lang)
    return out(clone((st.confirmed ? f.resultAfter : f.resultBefore)[lang]))
  }
  if (p === `/documents/${DEMO_ID}/schedule`) return out(scheduleView(f))
  if (p === `/documents/${DEMO_ID}/schedule-overrides` && method === 'PUT') {
    st.overrides = { ...(body.overrides ?? {}) }
    return out(scheduleView(f))
  }
  if (p === '/adherence' && method === 'POST') {
    const i = st.events.findIndex((e) => e.med_ref === body.med_ref && e.scheduled_time === body.scheduled_time && e.date === body.date)
    const ev: Event = { id: i >= 0 ? st.events[i].id : `demo-event-${++st.seq}`, document_id: DEMO_ID, med_ref: body.med_ref, scheduled_time: body.scheduled_time, date: body.date, status: body.status }
    if (i >= 0) st.events[i] = ev
    else st.events.push(ev)
    return out(ev)
  }
  if (p === '/adherence' && method === 'GET') return out({ events: clone(st.events).filter((e) => (!q.get('from') || e.date >= q.get('from')!) && (!q.get('to') || e.date <= q.get('to')!)) })
  const ae = p.match(/^\/adherence\/(.+)$/)
  if (ae && method === 'DELETE') {
    st.events = st.events.filter((e) => e.id !== ae[1])
    return out(undefined)
  }
  if (p === `/documents/${DEMO_ID}/doctor-summary`) return out(summaryView(f))
  // everything else a real session would offer (upload, delete my data, retry...) does not exist in the sample
  throw bad(404, 'not_found')
}
