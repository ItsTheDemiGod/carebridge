/* Small typed fetch wrapper for the CareBridge backend (/api/v1). Never logs request or response bodies. */

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  /** status 0 means the server could not be reached at all (code "network_error"). */
  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const STATE_CHANGING = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

type Options = { method?: string; body?: unknown; signal?: AbortSignal }

export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  const method = (opts.method ?? 'GET').toUpperCase()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (STATE_CHANGING.has(method)) headers['X-CareBridge-Request'] = '1'
  let body: BodyInit | undefined
  if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.body)
  }
  let res: Response
  try {
    res = await fetch(path, { method, headers, body, credentials: 'include', signal: opts.signal })
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e
    throw new ApiError(0, 'network_error', 'network_error')
  }
  if (res.status === 204) return undefined as T
  let data: unknown = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON body: handled below */
  }
  if (!res.ok) {
    const err = (data as { error?: { code?: string; message?: string } } | null)?.error
    throw new ApiError(res.status, err?.code ?? 'unknown_error', err?.message ?? '')
  }
  return data as T
}

/* Types only for the endpoints used in Phase 6a. */
export type Lang = 'en' | 'ta' | 'hi'
export type Health = { status: string; app: string; version: string }
export type ConsentNotice = {
  version: string
  language: Lang
  sha256: string
  title: string
  items: { id: string; text: string }[]
  purposes: { id: string; label: string; required?: boolean }[]
  review_status: string
}
export type StringsResponse = { language: Lang; strings: Record<string, string>; draft_unreviewed: boolean }

export const getHealth = (signal?: AbortSignal) => api<Health>('/api/health', { signal })
export const getConsentNotice = (lang: Lang, signal?: AbortSignal) => api<ConsentNotice>(`/api/v1/consent-notice?lang=${lang}`, { signal })
export const getStrings = (lang: Lang, prefix = '', signal?: AbortSignal) => api<StringsResponse>(`/api/v1/strings?lang=${lang}&prefix=${encodeURIComponent(prefix)}`, { signal })
