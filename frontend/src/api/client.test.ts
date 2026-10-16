import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, getConsentNotice } from './client'

const reply = (status: number, body?: unknown) => Promise.resolve(new Response(body === undefined ? null : JSON.stringify(body), { status }))
afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('always sends credentials and adds the request header only on state-changing methods', async () => {
    const f = vi.fn(() => reply(200, { ok: 1 }))
    vi.stubGlobal('fetch', f)
    await api('/x')
    await api('/x', { method: 'post', body: { a: 1 } })
    await api('/x', { method: 'DELETE' })
    const calls = f.mock.calls as unknown as [string, RequestInit][]
    expect(calls.every(([, i]) => i.credentials === 'include')).toBe(true)
    expect((calls[0][1].headers as Record<string, string>)['X-CareBridge-Request']).toBeUndefined()
    expect((calls[1][1].headers as Record<string, string>)['X-CareBridge-Request']).toBe('1')
    expect((calls[2][1].headers as Record<string, string>)['X-CareBridge-Request']).toBe('1')
    expect(calls[1][1].body).toBe('{"a":1}')
  })

  it('turns the backend error format into one error type', async () => {
    vi.stubGlobal('fetch', () => reply(403, { error: { code: 'consent_required', message: 'Please accept first.' } }))
    const e = await api('/x').catch((x) => x)
    expect(e).toBeInstanceOf(ApiError)
    expect([e.status, e.code, e.message]).toEqual([403, 'consent_required', 'Please accept first.'])
  })

  it('maps an unreachable server to status 0 / network_error and 204 to undefined', async () => {
    vi.stubGlobal('fetch', () => Promise.reject(new TypeError('failed')))
    const e = await api('/x').catch((x) => x)
    expect([e.status, e.code]).toEqual([0, 'network_error'])
    vi.stubGlobal('fetch', () => reply(204))
    expect(await api('/x')).toBeUndefined()
  })

  it('never logs request or response bodies', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((m) => vi.spyOn(console, m).mockImplementation(() => {}))
    vi.stubGlobal('fetch', () => reply(500, { error: { code: 'internal_error', message: 'secret-body' } }))
    await api('/x', { method: 'POST', body: { name: 'secret-body' } }).catch(() => {})
    expect(spies.every((s) => s.mock.calls.length === 0)).toBe(true)
    spies.forEach((s) => s.mockRestore())
  })

  it('requests the consent notice in the chosen language', async () => {
    const f = vi.fn(() => reply(200, { version: '2' }))
    vi.stubGlobal('fetch', f)
    await getConsentNotice('ta')
    expect((f.mock.calls as unknown as [string][])[0][0]).toBe('/api/v1/consent-notice?lang=ta')
  })
})
