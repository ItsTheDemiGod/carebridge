/* One typed function per backend endpoint. Paths are checked against docs/openapi.json by endpoints.test.ts. */
import { api } from './client'
import type { AdherenceIn, Confirmations, OverridesIn } from './openapi.generated'
import type {
  AdherenceEvent, ConfirmResponse, ConsentNotice, DeleteReceipt, DocView, DoctorSummary, FormularyEntry, FormularySearch, Lang, MedicinesResponse,
  ResultResponse, ScheduleResponse, SessionState, StringsResponse,
} from './types'

const V = '/api/v1'
type S = AbortSignal | undefined
const q = (o: Record<string, string | undefined>) => {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(o)) if (v) p.set(k, v)
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const consentNotice = (lang: Lang, signal?: S) => api<ConsentNotice>(`${V}/consent-notice${q({ lang })}`, { signal })
export const strings = (lang: Lang, prefix = '', signal?: S) => api<StringsResponse>(`${V}/strings${q({ lang, prefix })}`, { signal })
export const createSession = (language: Lang, signal?: S) => api<SessionState>(`${V}/sessions`, { method: 'POST', body: { language }, signal })
export const getSession = (signal?: S) => api<SessionState>(`${V}/session`, { signal })
export const giveConsent = (notice_version: string, purposes: string[], signal?: S) => api<SessionState>(`${V}/consent`, { method: 'POST', body: { notice_version, purposes }, signal })
export const deleteSession = (signal?: S) => api<DeleteReceipt | undefined>(`${V}/session`, { method: 'DELETE', signal })

export const uploadDocument = (file: Blob, type: string, signal?: S) => api<DocView>(`${V}/documents`, { method: 'POST', raw: { data: file, type }, signal })
export const listDocuments = (signal?: S) => api<{ documents: DocView[] }>(`${V}/documents`, { signal })
export const getDocument = (id: string, signal?: S) => api<DocView>(`${V}/documents/${id}`, { signal })
export const getDocumentImage = (id: string, signal?: S) => api<Blob>(`${V}/documents/${id}/image`, { blob: true, signal })
export const retryDocument = (id: string, signal?: S) => api<DocView>(`${V}/documents/${id}/retry`, { method: 'POST', signal })
export const startLanguage = (id: string, language: Lang, signal?: S) => api<DocView>(`${V}/documents/${id}/languages`, { method: 'POST', body: { language }, signal })

export const getMedicines = (id: string, signal?: S) => api<MedicinesResponse>(`${V}/documents/${id}/medicines`, { signal })
export const saveConfirmations = (id: string, body: Confirmations, signal?: S) => api<ConfirmResponse>(`${V}/documents/${id}/confirmations`, { method: 'POST', body, signal })
export const searchFormulary = (text: string, limit = 20, signal?: S) => api<FormularySearch>(`${V}/formulary/search${q({ q: text, limit: String(limit) })}`, { signal })
export const getFormularyEntry = (fid: string, signal?: S) => api<FormularyEntry & { formulary_status: string }>(`${V}/formulary/${encodeURIComponent(fid)}`, { signal })

export const getResult = (id: string, lang: Lang, signal?: S) => api<ResultResponse>(`${V}/documents/${id}/result${q({ lang })}`, { signal })
export const getSchedule = (id: string, signal?: S) => api<ScheduleResponse>(`${V}/documents/${id}/schedule`, { signal })
export const saveOverrides = (id: string, body: OverridesIn, signal?: S) => api<ScheduleResponse>(`${V}/documents/${id}/schedule-overrides`, { method: 'PUT', body, signal })
export const logAdherence = (body: AdherenceIn, signal?: S) => api<AdherenceEvent>(`${V}/adherence`, { method: 'POST', body, signal })
export const listAdherence = (document_id: string, from?: string, to?: string, signal?: S) => api<{ events: AdherenceEvent[] }>(`${V}/adherence${q({ document_id, from, to })}`, { signal })
export const deleteAdherence = (eventId: string, signal?: S) => api<undefined>(`${V}/adherence/${eventId}`, { method: 'DELETE', signal })
export const getDoctorSummary = (id: string, from?: string, to?: string, signal?: S) => api<DoctorSummary>(`${V}/documents/${id}/doctor-summary${q({ from, to })}`, { signal })
