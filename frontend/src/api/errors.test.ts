import { describe, expect, it } from 'vitest'
import { ApiError } from './client'
import { isSessionProblem, toProblem } from './errors'

const e = (status: number, code: string, retry: number | null = null) => Object.assign(new ApiError(status, code, ''), { retryAfter: retry })

describe('error mapping', () => {
  it.each([
    [0, 'network_error', 'network'],
    [401, 'session_expired', 'expired'],
    [401, 'no_session', 'expired'],
    [403, 'consent_required', 'consent_required'],
    [403, 'request_blocked', 'blocked'],
    [404, 'not_found', 'not_found'],
    [409, 'not_ready', 'not_ready'],
    [413, 'upload_too_large', 'too_large'],
    [415, 'pdf_not_supported', 'pdf'],
    [415, 'unsupported_file', 'unsupported'],
    [422, 'image_invalid', 'invalid'],
    [429, 'queue_full', 'queue_full'],
    [429, 'too_many_documents', 'too_many_documents'],
    [500, 'internal_error', 'server'],
  ])('%i %s -> %s', (status, code, kind) => expect(toProblem(e(status, code)).kind).toBe(kind))
  it('carries Retry-After and flags session-level problems', () => {
    expect(toProblem(e(429, 'queue_full', 60)).retryAfter).toBe(60)
    expect(isSessionProblem(toProblem(e(401, 'x')))).toBe(true)
    expect(isSessionProblem(toProblem(e(404, 'x')))).toBe(false)
    expect(toProblem(new Error('x')).kind).toBe('unknown')
  })
})
