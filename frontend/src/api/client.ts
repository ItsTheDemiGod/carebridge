/* Small typed fetch wrapper for the CareBridge backend (/api/v1). Never logs request or response bodies. */

import { ApiError } from './apiError'
import { demoApi, isDemoPath } from '../demo/demoApi'
import { DEMO_ONLY } from '../lib/mode'

export { ApiError }

const STATE_CHANGING = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

export type Options = { method?: string; body?: unknown; raw?: { data: Blob; type: string }; blob?: boolean; signal?: AbortSignal }

export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  // the sample (/demo) is answered from bundled fixtures in memory: no request leaves the page
  if (DEMO_ONLY || (typeof window !== 'undefined' && isDemoPath(window.location.pathname))) return demoApi<T>(path, opts) // hosted sample: no request ever leaves the page
  const method = (opts.method ?? 'GET').toUpperCase()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (STATE_CHANGING.has(method)) headers['X-CareBridge-Request'] = '1'
  let body: BodyInit | undefined
  if (opts.raw) {
    headers['Content-Type'] = opts.raw.type // raw file body (upload): sent once, never stored
    body = opts.raw.data
  } else if (opts.body !== undefined) {
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
  if (opts.blob && res.ok) return (await res.blob()) as T
  let data: unknown = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON body: handled below */
  }
  if (!res.ok) {
    const err = (data as { error?: { code?: string; message?: string } } | null)?.error
    const e = new ApiError(res.status, err?.code ?? 'unknown_error', err?.message ?? '')
    const ra = Number(res.headers.get('Retry-After'))
    e.retryAfter = Number.isFinite(ra) && ra > 0 ? ra : null
    throw e
  }
  return data as T
}

export type { Lang, Health, ConsentNotice, StringsResponse } from './types'
import type { ConsentNotice, Health, Lang, StringsResponse } from './types'

export const getHealth = (signal?: AbortSignal) => api<Health>('/api/health', { signal })
export const getConsentNotice = (lang: Lang, signal?: AbortSignal) => api<ConsentNotice>(`/api/v1/consent-notice?lang=${lang}`, { signal })
export const getStrings = (lang: Lang, prefix = '', signal?: AbortSignal) => api<StringsResponse>(`/api/v1/strings?lang=${lang}&prefix=${encodeURIComponent(prefix)}`, { signal })
