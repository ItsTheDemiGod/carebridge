import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/apiError'
import type { AdherenceEvent, ConfirmResponse, DocView, DoctorSummary, FormularySearch, MedicinesResponse, ResultResponse, ScheduleResponse, SessionState } from '../api/types'
import { demoApi, DEMO_IMAGE, isDemoPath, resetDemo } from './demoApi'
import { fixtures, meta } from './fixtures'

const fetched: string[] = []
beforeEach(() => {
  fetched.length = 0
  resetDemo()
  // the ONLY thing the sample may fetch is its own static photo; anything else (an /api call) is recorded and fails the test
  vi.stubGlobal('fetch', async (u: string) => {
    fetched.push(String(u))
    return { blob: async () => new Blob(['png']) }
  })
})

const get = <T,>(p: string) => demoApi<T>(p)
const post = <T,>(p: string, body: unknown) => demoApi<T>(p, { method: 'POST', body })

describe('route test', () => {
  it('only /demo and below are the sample', () => {
    expect(['/demo', '/demo/review', '/demo/result'].every(isDemoPath)).toBe(true)
    expect(['/', '/demonstration', '/d/x/review', '/start', '/how-we-tested-it'].some(isDemoPath)).toBe(false)
  })
})

describe('DemoApi', () => {
  it('answers a whole visit from memory and fetches nothing but the sample photo', async () => {
    const s = await get<SessionState>('/api/v1/session')
    expect(s.consent.granted).toBe(true)
    await get('/api/v1/strings?lang=en&prefix=')
    await get<DocView>('/api/v1/documents/demo')
    const m = await get<MedicinesResponse>('/api/v1/documents/demo/medicines')
    expect(m.medicines.length).toBeGreaterThanOrEqual(3)
    await post('/api/v1/documents/demo/confirmations', fixtures.scriptedDecisions)
    await get<ResultResponse>('/api/v1/documents/demo/result?lang=hi')
    await get<ScheduleResponse>('/api/v1/documents/demo/schedule')
    await get<DoctorSummary>('/api/v1/documents/demo/doctor-summary')
    expect(fetched).toEqual([DEMO_IMAGE])
    expect(fetched.some((u) => u.includes('/api'))).toBe(false)
  })

  it('shows the recorded BEFORE state, then the recorded AFTER state whatever was chosen, in every language', async () => {
    for (const lang of ['en', 'ta', 'hi'] as const) {
      resetDemo()
      await post('/api/v1/sessions', { language: lang })
      const b = await get<ResultResponse>(`/api/v1/documents/demo/result?lang=${lang}`)
      expect(b.confirmed).toBe(false)
      expect(b.confirm_first).toBe(true)
      const before = await get<MedicinesResponse>('/api/v1/documents/demo/medicines')
      expect(before.medicines.some((x) => x.review_level === 'must_confirm' && x.current_decision === null)).toBe(true)
      // the person decides something else entirely: the answer is still the recorded one
      const r = await post<ConfirmResponse>('/api/v1/documents/demo/confirmations', { decisions: [{ index: 0, action: 'remove' }] })
      expect(r).toEqual(fixtures.confirmResponse)
      const after = await get<ResultResponse>(`/api/v1/documents/demo/result?lang=${lang}`)
      expect(after.confirmed).toBe(true)
      expect(after).toEqual(fixtures.resultAfter[lang])
    }
  })

  it('rejects a confirmation without decisions like the real API', async () => {
    await expect(post('/api/v1/documents/demo/confirmations', {})).rejects.toMatchObject({ status: 422 })
  })

  it('serves the formulary: recorded searches match, entries exist, unknown ids are 404', async () => {
    for (const [q, rec] of Object.entries(fixtures.formulary.searches)) {
      const r = await get<FormularySearch>(`/api/v1/formulary/search?q=${q}&limit=20`)
      expect(r.results.map((e) => e.id).sort()).toEqual((rec as FormularySearch).results.map((e) => e.id).sort())
    }
    expect((await get<FormularySearch>('/api/v1/formulary/search?q=metf')).results[0].generic).toBe('Metformin')
    expect((await get<FormularySearch>('/api/v1/formulary/search?q=')).results).toEqual([])
    expect(await get('/api/v1/formulary/metformin')).toMatchObject({ id: 'metformin' })
    await expect(get('/api/v1/formulary/nope')).rejects.toBeInstanceOf(ApiError)
  })

  it('keeps taken/skipped marks in memory only and forgets them on reset', async () => {
    const e = await post<AdherenceEvent>('/api/v1/adherence', { document_id: 'demo', med_ref: 'm0', scheduled_time: '08:30', date: '2026-01-01', status: 'taken' })
    const e2 = await post<AdherenceEvent>('/api/v1/adherence', { document_id: 'demo', med_ref: 'm0', scheduled_time: '08:30', date: '2026-01-01', status: 'skipped' })
    expect(e2.id).toBe(e.id) // same slot: replaced, not duplicated
    expect((await get<{ events: AdherenceEvent[] }>('/api/v1/adherence?document_id=demo')).events).toHaveLength(1)
    const sum = await get<DoctorSummary>('/api/v1/documents/demo/doctor-summary')
    expect(sum.medicines.find((m) => m.ref === 'm0')).toMatchObject({ taken: 0, skipped: 1 })
    await demoApi('/api/v1/adherence/' + e.id, { method: 'DELETE' })
    expect((await get<{ events: AdherenceEvent[] }>('/api/v1/adherence?document_id=demo')).events).toHaveLength(0)
    await post('/api/v1/adherence', { document_id: 'demo', med_ref: 'm1', scheduled_time: '08:00', date: '2026-01-01', status: 'taken' })
    resetDemo()
    expect((await get<{ events: AdherenceEvent[] }>('/api/v1/adherence?document_id=demo')).events).toHaveLength(0)
  })

  it('applies edited times in memory and marks the medicine as user-set', async () => {
    const base = await get<ScheduleResponse>('/api/v1/documents/demo/schedule')
    const ref = base.medicines[0].ref
    const r = await demoApi<ScheduleResponse>('/api/v1/documents/demo/schedule-overrides', { method: 'PUT', body: { overrides: { [ref]: ['09:15'] } } })
    expect(r.medicines.find((m) => m.ref === ref)).toMatchObject({ times: ['09:15'], source: 'user' })
    expect(r.slots.filter((s) => s.med_ref === ref).map((s) => s.time)).toEqual(['09:15'])
  })

  it('has no upload, no delete-my-data and no session of its own: those paths do not exist', async () => {
    await expect(demoApi('/api/v1/documents', { method: 'POST', raw: { data: new Blob(['x']), type: 'image/png' } })).rejects.toMatchObject({ status: 404 })
    await expect(demoApi('/api/v1/session', { method: 'DELETE' })).rejects.toMatchObject({ status: 404 })
  })

  it('is recorded from the synthetic dev document and says so', () => {
    expect(meta.source_document).toBe('ds_037')
    expect(meta.condition).toBe('poor')
  })
})

describe('fixtures vs the response types the pages use (required keys)', () => {
  const keys = (o: object, ks: string[]) => ks.filter((k) => !(k in o))
  it('medicines, result, schedule, summary, session, document', () => {
    for (const lang of ['en', 'ta', 'hi'] as const) {
      const mb = fixtures.medicinesBefore[lang] as MedicinesResponse
      const ma = fixtures.medicinesAfter[lang] as MedicinesResponse
      for (const m of [...mb.medicines, ...ma.medicines])
        expect(keys(m, ['index', 'ref', 'as_written', 'printed', 'strength', 'frequency', 'source_quote', 'review_level', 'reasons', 'interaction_ready', 'schedule_ready', 'allowed_actions', 'current_decision'])).toEqual([])
      expect(keys(mb, ['medicines', 'added_medicines', 'dose_options', 'strength_as_label_option', 'formulary_status', 'compare_note'])).toEqual([])
      for (const r of [fixtures.resultBefore[lang], fixtures.resultAfter[lang]] as object[])
        expect(keys(r, ['document_id', 'language', 'confirmed', 'confirm_first', 'narrative_status', 'explanation', 'medicines_meta', 'removed', 'guardrail_events'])).toEqual([])
      expect(keys(fixtures.schedule[lang] as object, ['document_id', 'language', 'notice', 'extra_notices', 'slots', 'medicines', 'not_scheduled', 'guardrail_events'])).toEqual([])
      expect(keys(fixtures.doctorSummary[lang] as object, ['document_id', 'language', 'title', 'period', 'headings', 'labels', 'medicines', 'unconfirmed', 'not_scheduled', 'interactions', 'schedule_notice', 'disclaimer', 'guardrail_events'])).toEqual([])
    }
    expect(keys(fixtures.session, ['language', 'expires_at', 'consent', 'documents', 'limits'])).toEqual([])
    expect(keys(fixtures.document, ['id', 'state', 'error_code', 'narrative', 'timings', 'retry_possible', 'confirmed', 'image_kept'])).toEqual([])
  })
})
