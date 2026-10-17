import { describe, expect, it } from 'vitest'
import type { DocView, SessionState } from '../api/types'
import { consentGranted, flowReducer, initialFlow, isFlowPath, routeForDoc, stageForPath } from './state'

const sess = (granted: boolean): SessionState => ({ language: 'en', expires_at: 'x', consent: { granted, current_version: '2', purposes: [] }, documents: 0, limits: { max_documents: 10, max_upload_bytes: 1 } })
const doc = (id: string, state: DocView['state'] = 'queued'): DocView => ({ id, state, error_code: null, error_message: null, created_at: '', updated_at: '', image_kept: false, narrative: {}, timings: {}, retry_possible: false, confirmed: false })

describe('flow reducer', () => {
  it('boots to ready with the session and its language', () => {
    let s = flowReducer(initialFlow, { type: 'boot_start' })
    expect(s.boot).toBe('loading')
    s = flowReducer(s, { type: 'session_ok', session: sess(true), docs: [doc('a')] })
    expect([s.boot, s.sessionLang, s.docs.length, consentGranted(s)]).toEqual(['ready', 'en', 1, true])
  })
  it('upserts documents by id', () => {
    let s = flowReducer(initialFlow, { type: 'doc_upsert', doc: doc('a') })
    s = flowReducer(s, { type: 'doc_upsert', doc: doc('a', 'awaiting_confirmation') })
    s = flowReducer(s, { type: 'doc_upsert', doc: doc('b') })
    expect(s.docs.map((d) => [d.id, d.state])).toEqual([['a', 'awaiting_confirmation'], ['b', 'queued']])
  })
  it('a 401 clears the session, documents and unsaved state but keeps the problem', () => {
    let s = flowReducer(initialFlow, { type: 'session_ok', session: sess(true), docs: [doc('a')] })
    s = flowReducer(s, { type: 'dirty', dirty: true })
    s = flowReducer(s, { type: 'no_session', problem: { kind: 'expired', code: 'session_expired', status: 401, retryAfter: null } })
    expect([s.boot, s.session, s.docs, s.dirty, s.problem?.kind]).toEqual(['no_session', null, [], false, 'expired'])
  })
  it('consent_required marks consent as not granted', () => {
    let s = flowReducer(initialFlow, { type: 'session_ok', session: sess(true) })
    s = flowReducer(s, { type: 'problem', problem: { kind: 'consent_required', code: 'consent_required', status: 403, retryAfter: null } })
    expect(consentGranted(s)).toBe(false)
  })
  it('reset (delete my data) clears everything held in memory', () => {
    let s = flowReducer(initialFlow, { type: 'session_ok', session: sess(true), docs: [doc('a')] })
    s = flowReducer(s, { type: 'photo', url: 'blob:x' })
    s = flowReducer(s, { type: 'reset' })
    expect([s.session, s.docs, s.photoUrl, s.dirty, s.boot]).toEqual([null, [], null, false, 'no_session'])
  })
  it('routes documents and stages', () => {
    expect(routeForDoc(doc('a', 'extracting'))).toBe('/d/a/processing')
    expect(routeForDoc(doc('a', 'awaiting_confirmation'))).toBe('/d/a/review')
    expect([stageForPath('/consent'), stageForPath('/d/x/processing'), stageForPath('/d/x/review'), stageForPath('/d/x/result'), stageForPath('/d/x/summary'), stageForPath('/privacy')]).toEqual(['consent', 'photo', 'check', 'results', 'schedule', null])
    expect([isFlowPath('/upload'), isFlowPath('/d/x/result'), isFlowPath('/privacy'), isFlowPath('/')]).toEqual([true, true, false, false])
  })
})
