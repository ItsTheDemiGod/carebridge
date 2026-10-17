import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { toProblem, isAbort, type Problem } from '../api/errors'
import * as API from '../api/endpoints'
import type { DeleteReceipt, DocView, Lang } from '../api/types'
import { useT } from '../i18n/I18n'
import { flowReducer, initialFlow, isFlowPath, type FlowState } from './state'

export type FlowApi = {
  state: FlowState
  /** create (or resume) the session in the current language; resolves with null on success */
  startSession: () => Promise<Problem | null>
  giveConsent: (version: string, purposes: string[]) => Promise<Problem | null>
  refreshDocs: () => Promise<DocView[]>
  upsertDoc: (d: DocView) => void
  /** map an error; a 401 drops the session, a 403 consent_required marks consent missing. Returns the mapped problem for inline display. */
  report: (e: unknown) => Problem
  setPhoto: (blob: Blob | null) => void
  setDirty: (d: boolean) => void
  deleteAll: () => Promise<DeleteReceipt | null>
  clearProblem: () => void
  retryBoot: () => void
}
const Ctx = createContext<FlowApi | null>(null)

export function FlowProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(flowReducer, initialFlow)
  const { lang } = useT()
  const loc = useLocation()
  const langRef = useRef<Lang>(lang)
  langRef.current = lang
  const photoRef = useRef<string | null>(null)

  const report = useCallback((e: unknown): Problem => {
    const p = toProblem(e)
    if (p.kind === 'expired') dispatch({ type: 'no_session', problem: p })
    else if (p.kind === 'consent_required') dispatch({ type: 'problem', problem: p })
    return p
  }, [])

  const setPhoto = useCallback((blob: Blob | null) => {
    if (photoRef.current) URL.revokeObjectURL(photoRef.current)
    photoRef.current = blob ? URL.createObjectURL(blob) : null
    dispatch({ type: 'photo', url: photoRef.current })
  }, [])

  const boot = useCallback(async () => {
    dispatch({ type: 'boot_start' })
    try {
      let session = await API.getSession()
      if (session.language !== langRef.current) session = await API.createSession(langRef.current)
      const docs = session.consent.granted ? (await API.listDocuments()).documents : []
      dispatch({ type: 'session_ok', session, docs })
    } catch (e) {
      const p = toProblem(e)
      if (p.kind === 'expired') dispatch({ type: 'no_session', problem: null }) // simply no session yet
      else if (p.kind === 'consent_required') dispatch({ type: 'boot_error', problem: p })
      else dispatch({ type: 'boot_error', problem: p })
    }
  }, [])

  // rebuild from the server on any flow page (no client persistence of results); other pages never touch the API
  const flow = isFlowPath(loc.pathname)
  useEffect(() => {
    if (flow && state.boot === 'idle') void boot()
  }, [flow, state.boot, boot])

  // a language change is sent to the server so server-written text follows it
  useEffect(() => {
    if (state.boot === 'ready' && state.sessionLang && state.sessionLang !== lang) {
      API.createSession(lang)
        .then((session) => dispatch({ type: 'session_ok', session }))
        .catch((e) => void report(e))
    }
  }, [lang, state.boot, state.sessionLang, report])

  // the photo preview lives only while the person is inside the flow
  useEffect(() => {
    if (!flow && photoRef.current) setPhoto(null)
  }, [flow, setPhoto])
  useEffect(() => () => {
    if (photoRef.current) URL.revokeObjectURL(photoRef.current)
  }, [])

  const api = useMemo<FlowApi>(
    () => ({
      state,
      startSession: async () => {
        try {
          const session = await API.createSession(langRef.current)
          const docs = session.consent.granted ? (await API.listDocuments()).documents : []
          dispatch({ type: 'session_ok', session, docs })
          return null
        } catch (e) {
          return isAbort(e) ? null : report(e)
        }
      },
      giveConsent: async (version, purposes) => {
        try {
          dispatch({ type: 'session_ok', session: await API.giveConsent(version, purposes) })
          return null
        } catch (e) {
          return report(e)
        }
      },
      refreshDocs: async () => {
        try {
          const docs = (await API.listDocuments()).documents
          dispatch({ type: 'docs_set', docs })
          return docs
        } catch (e) {
          report(e)
          return []
        }
      },
      upsertDoc: (doc) => dispatch({ type: 'doc_upsert', doc }),
      report,
      setPhoto,
      setDirty: (dirty) => dispatch({ type: 'dirty', dirty }),
      deleteAll: async () => {
        try {
          const receipt = (await API.deleteSession()) ?? null
          setPhoto(null)
          dispatch({ type: 'reset' })
          dispatch({ type: 'deleted', receipt })
          return receipt ?? ({ deleted: {}, deleted_at: '', message: '', receipt: '' } satisfies DeleteReceipt)
        } catch (e) {
          if (report(e).kind === 'expired') {
            // the session was already gone: nothing is left to delete
            setPhoto(null)
            dispatch({ type: 'reset' })
            return { deleted: {}, deleted_at: '', message: '', receipt: '' } satisfies DeleteReceipt
          }
          return null
        }
      },
      clearProblem: () => dispatch({ type: 'problem', problem: null }),
      retryBoot: () => void boot(),
    }),
    [state, report, setPhoto, boot],
  )
  return <Ctx.Provider value={api}>{children}</Ctx.Provider>
}

export function useFlow(): FlowApi {
  const c = useContext(Ctx)
  if (!c) throw new Error('useFlow needs FlowProvider')
  return c
}
