/* Flow state: a small reducer, no library. NOTHING here is persisted: a reload rebuilds it from GET /session and GET /documents.
 * The only client storage in the whole app is language and calm mode (lib/prefs.ts). */
import type { Problem } from '../api/errors'
import type { DeleteReceipt, DocView, Lang, SessionState } from '../api/types'

export type FlowState = {
  boot: 'idle' | 'loading' | 'ready' | 'no_session' | 'error'
  session: SessionState | null
  /** language the backend session currently uses (pages refetch server text when it changes) */
  sessionLang: Lang | null
  docs: DocView[]
  /** latest session-level problem (expired, consent_required, network on boot) */
  problem: Problem | null
  /** unsaved medicine decisions exist: leaving asks for confirmation */
  dirty: boolean
  /** object URL of the chosen photo (memory only, revoked on leave/delete) */
  photoUrl: string | null
  /** shown on the landing page after delete-my-data */
  deleted: DeleteReceipt | null
}

export const initialFlow: FlowState = { boot: 'idle', session: null, sessionLang: null, docs: [], problem: null, dirty: false, photoUrl: null, deleted: null }

export type FlowAction =
  | { type: 'boot_start' }
  | { type: 'session_ok'; session: SessionState; docs?: DocView[] }
  | { type: 'no_session'; problem?: Problem | null }
  | { type: 'boot_error'; problem: Problem }
  | { type: 'docs_set'; docs: DocView[] }
  | { type: 'doc_upsert'; doc: DocView }
  | { type: 'problem'; problem: Problem | null }
  | { type: 'dirty'; dirty: boolean }
  | { type: 'photo'; url: string | null }
  | { type: 'deleted'; receipt: DeleteReceipt | null }
  | { type: 'reset' }

export function flowReducer(s: FlowState, a: FlowAction): FlowState {
  switch (a.type) {
    case 'boot_start':
      return s.boot === 'idle' || s.boot === 'error' || s.boot === 'no_session' ? { ...s, boot: 'loading', problem: null } : s
    case 'session_ok':
      return { ...s, boot: 'ready', session: a.session, sessionLang: a.session.language, docs: a.docs ?? s.docs, problem: null, deleted: null }
    case 'no_session':
      // 401: the session (and its data) is gone; drop everything held in memory except the problem so the UI can explain
      return { ...initialFlow, boot: 'no_session', problem: a.problem ?? null, photoUrl: s.photoUrl, deleted: s.deleted }
    case 'boot_error':
      return { ...s, boot: 'error', problem: a.problem }
    case 'docs_set':
      return { ...s, docs: a.docs }
    case 'doc_upsert': {
      const i = s.docs.findIndex((d) => d.id === a.doc.id)
      const docs = i < 0 ? [...s.docs, a.doc] : s.docs.map((d, k) => (k === i ? a.doc : d))
      return { ...s, docs }
    }
    case 'problem':
      if (a.problem?.kind === 'consent_required' && s.session) return { ...s, problem: a.problem, session: { ...s.session, consent: { ...s.session.consent, granted: false } } }
      return { ...s, problem: a.problem }
    case 'dirty':
      return s.dirty === a.dirty ? s : { ...s, dirty: a.dirty }
    case 'photo':
      return { ...s, photoUrl: a.url }
    case 'deleted':
      return { ...s, deleted: a.receipt }
    case 'reset':
      return { ...initialFlow, boot: 'no_session' }
  }
}

export const consentGranted = (s: FlowState) => !!s.session?.consent.granted
export const docById = (s: FlowState, id: string | undefined) => s.docs.find((d) => d.id === id)

/** Where a document in this state belongs in the flow. */
export function routeForDoc(d: Pick<DocView, 'id' | 'state'>): string {
  return d.state === 'awaiting_confirmation' ? `/d/${d.id}/review` : `/d/${d.id}/processing`
}

/** Flow stage for the progress indicator (consent, photo, check, results, schedule), by route path. */
export const STAGES = ['consent', 'photo', 'check', 'results', 'schedule'] as const
export type Stage = (typeof STAGES)[number]
export function stageForPath(path: string): Stage | null {
  if (path === '/consent' || path === '/start') return 'consent'
  if (path === '/upload' || /^\/d\/[^/]+\/processing$/.test(path)) return 'photo'
  if (/^\/d\/[^/]+\/review$/.test(path)) return 'check'
  if (/^\/d\/[^/]+\/result$/.test(path)) return 'results'
  if (/^\/d\/[^/]+\/(schedule|summary)$/.test(path)) return 'schedule'
  return null
}
export const isFlowPath = (path: string) => /^\/(start|consent|upload|documents)$/.test(path) || /^\/d\/[^/]+\//.test(path)
