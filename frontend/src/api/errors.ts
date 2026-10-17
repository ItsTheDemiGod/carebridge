/* One mapping from the backend error format (ApiError) to what the UI does about it. Pure; no text here:
 * the UI looks up `ui.flow.problem.<kind>` for client-side wording and `error.<code>` (GET /strings) for the backend's own message. */
import { ApiError } from './client'

export type ProblemKind =
  | 'expired' // 401: no/expired session; its data is gone
  | 'consent_required' // 403 consent_required: go to the consent step
  | 'blocked' // 403 request_blocked
  | 'not_found' // 404 (also another session's id)
  | 'not_ready' // 409 not_ready / retry_unavailable
  | 'queue_full' // 429 queue_full (Retry-After)
  | 'too_many_documents' // 429
  | 'too_large' // 413
  | 'pdf' // 415 pdf_not_supported
  | 'unsupported' // 415 unsupported_file
  | 'invalid' // 400/422
  | 'network' // server unreachable
  | 'server' // 5xx
  | 'unknown'

export type Problem = { kind: ProblemKind; code: string; status: number; retryAfter: number | null }

export function toProblem(e: unknown): Problem {
  if (!(e instanceof ApiError)) return { kind: 'unknown', code: 'unknown_error', status: 0, retryAfter: null }
  const { status, code } = e
  const kind = ((): ProblemKind => {
    if (status === 0) return 'network'
    if (status === 401) return 'expired'
    if (status === 403) return code === 'consent_required' ? 'consent_required' : 'blocked'
    if (status === 404) return 'not_found'
    if (status === 409) return 'not_ready'
    if (status === 413) return 'too_large'
    if (status === 415) return code === 'pdf_not_supported' ? 'pdf' : 'unsupported'
    if (status === 429) return code === 'too_many_documents' ? 'too_many_documents' : 'queue_full'
    if (status === 400 || status === 422) return 'invalid'
    if (status >= 500) return 'server'
    return 'unknown'
  })()
  return { kind, code, status, retryAfter: e.retryAfter }
}

export const isAbort = (e: unknown) => e instanceof DOMException && e.name === 'AbortError'

/** Problems after which the whole flow must restart or re-consent (as opposed to an inline, recoverable message). */
export const isSessionProblem = (p: Problem) => p.kind === 'expired' || p.kind === 'consent_required'
