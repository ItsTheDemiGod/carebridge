/* The error every API call (real or sample) throws. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  /** seconds from a Retry-After header (429 queue_full), else null */
  retryAfter: number | null = null
  /** status 0 means the server could not be reached at all (code "network_error"). */
  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}
