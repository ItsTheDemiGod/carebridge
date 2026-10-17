import { useEffect, useMemo, useRef, useState } from 'react'
import { useBlocker, useNavigate, useParams } from 'react-router-dom'
import { getDocument, getDocumentImage, getFormularyEntry, getMedicines, saveConfirmations } from '../../api/endpoints'
import { isAbort, type Problem } from '../../api/errors'
import type { ConfirmedSummary, FormularyEntry, MedicinesResponse } from '../../api/types'
import { Button, ButtonLink } from '../../components/Button'
import { Dialog } from '../../components/Dialog'
import { Notice } from '../../components/Badges'
import { Icon } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { attentionCount, buildConfirmations, draftFromServer, emptyDraft, MAX_ADDED, type AddedDraft, type Draft } from '../../flow/review'
import { useServerStrings } from '../../flow/serverStrings'
import { useT } from '../../i18n/I18n'
import { AddMedicine } from './review/AddMedicine'
import { MedicineCard } from './review/MedicineCard'
import { PhotoViewer } from './review/PhotoViewer'

export function ReviewPage() {
  const { id = '' } = useParams()
  return (
    <FlowPage titleKey="ui.title.review" narrow={false}>
      <Review id={id} />
    </FlowPage>
  )
}

const entryOrNull = (id: string | undefined | null) => (id ? getFormularyEntry(id).then((e) => e as FormularyEntry).catch(() => null) : Promise.resolve(null))

function Review({ id }: { id: string }) {
  const { t, lang } = useT()
  const { s } = useServerStrings()
  const flow = useFlow()
  const nav = useNavigate()
  const sessionLang = flow.state.sessionLang
  const [data, setData] = useState<MedicinesResponse | null>(null)
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [added, setAdded] = useState<AddedDraft[]>([])
  const [snapshot, setSnapshot] = useState('')
  const [loadProblem, setLoadProblem] = useState<Problem | null>(null)
  const [problem, setProblem] = useState<Problem | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState<Record<string, ConfirmedSummary> | null>(null)
  const [adding, setAdding] = useState(false)
  const [showPhoto, setShowPhoto] = useState(false)
  const [imageTried, setImageTried] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const savedRef = useRef<HTMLDivElement>(null)

  // load: the document must be waiting for confirmation, then the medicines (and any stored decisions, after a reload)
  useEffect(() => {
    if (!sessionLang) return
    const ctl = new AbortController()
    ;(async () => {
      try {
        const doc = await getDocument(id, ctl.signal)
        flow.upsertDoc(doc)
        if (doc.state !== 'awaiting_confirmation') {
          nav(`/d/${id}/processing`, { replace: true })
          return
        }
        const r = await getMedicines(id, ctl.signal)
        const entries = await Promise.all(r.medicines.map((m) => entryOrNull((m.current_decision as { formulary_id?: string } | null)?.formulary_id)))
        const d: Record<number, Draft> = {}
        r.medicines.forEach((m, i) => (d[m.index] = m.current_decision ? draftFromServer(m, entries[i]) : emptyDraft(m)))
        const ad = await Promise.all(
          r.added_medicines.map(async (a, k) => {
            const e = await entryOrNull(a.formulary_id as string)
            const sc = (a.schedule ?? {}) as { times_per_day?: number | string; timing_label?: string; duration_days?: number | null }
            return e ? ({ key: `srv-${k}`, formulary: e, strength: String(a.strength_choice), dose: String(a.dose), sched: { times: String(sc.times_per_day ?? ''), timing: sc.timing_label ?? 'unspecified', days: sc.duration_days ? String(sc.duration_days) : '' } } as AddedDraft) : null
          }),
        )
        const addedOk = ad.filter((x): x is AddedDraft => !!x)
        setData(r)
        setDrafts(d)
        setAdded(addedOk)
        setSnapshot(JSON.stringify(buildConfirmations(r.medicines, d, addedOk)))
        setLoadProblem(null)
      } catch (e) {
        if (!isAbort(e)) setLoadProblem(flow.report(e))
      }
    })()
    return () => ctl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, sessionLang, attempt])

  // the photo: the in-memory preview from the upload, else the server copy when the person chose to keep it
  const doc = flow.state.docs.find((d) => d.id === id)
  const photoUrl = flow.state.photoUrl
  useEffect(() => {
    if (photoUrl || imageTried || !doc?.image_kept) return
    setImageTried(true)
    getDocumentImage(id)
      .then((b) => flow.setPhoto(b))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [photoUrl, imageTried, doc?.image_kept, id])

  const payload = useMemo(() => (data ? buildConfirmations(data.medicines, drafts, added) : null), [data, drafts, added])
  const dirty = !!payload && JSON.stringify(payload) !== snapshot
  useEffect(() => flow.setDirty(dirty), [dirty]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => flow.setDirty(false), []) // eslint-disable-line react-hooks/exhaustive-deps
  const blocker = useBlocker(dirty)
  useEffect(() => {
    if (!dirty) return
    const h = (e: BeforeUnloadEvent) => e.preventDefault()
    window.addEventListener('beforeunload', h)
    return () => window.removeEventListener('beforeunload', h)
  }, [dirty])

  const save = async () => {
    if (!payload) return
    setSaving(true)
    setProblem(null)
    try {
      const r = await saveConfirmations(id, payload)
      setSaved(Object.fromEntries(r.medicines.map((m) => [m.ref, m])))
      setSnapshot(JSON.stringify(payload))
      flow.setDirty(false)
      requestAnimationFrame(() => savedRef.current?.focus())
    } catch (e) {
      setProblem(flow.report(e))
    }
    setSaving(false)
  }

  if (loadProblem) {
    return (
      <>
        <SectionHeading as="h1" label={t('ui.flow.stage.check')} title={t('ui.flow.review.title')} />
        <ProblemNotice problem={loadProblem} />
        <div className="page-actions">
          <Button variant="secondary" onClick={() => (setLoadProblem(null), setAttempt((n) => n + 1))}>{t('ui.flow.retry')}</Button>
          <ButtonLink to="/documents" variant="quiet">{t('ui.flow.nav.documents')}</ButtonLink>
        </div>
      </>
    )
  }
  if (!data) {
    return (
      <>
        <SectionHeading as="h1" label={t('ui.flow.stage.check')} title={t('ui.flow.review.title')} />
        <p role="status" className="muted">{t('ui.flow.loading')}</p>
      </>
    )
  }

  const left = attentionCount(data.medicines, drafts)
  const nothing = data.medicines.length === 0 && added.length === 0

  return (
    <>
      <SectionHeading as="h1" label={t('ui.flow.stage.check')} title={t('ui.flow.review.title')} />
      <p className="lede">{t('ui.flow.review.intro')}</p>
      <Notice tone="important" title={t('ui.flow.review.meaning.title')}>
        <p>{t('ui.flow.review.meaning')}</p>
        <p>{t('ui.flow.review.risk')}</p>
      </Notice>

      <div className="review-grid" lang={lang}>
        <aside className="review-photo" aria-label={t('ui.flow.photo.label')}>
          <button type="button" className="photo-toggle" aria-expanded={showPhoto} aria-controls="photo-pane" onClick={() => setShowPhoto((v) => !v)}>
            <Icon name="document" size={20} />
            <span>{showPhoto ? t('ui.flow.photo.hide') : t('ui.flow.photo.show')}</span>
          </button>
          <div id="photo-pane" className={`photo-pane${showPhoto ? ' open' : ''}`}>
            {photoUrl ? (
              <PhotoViewer url={photoUrl} />
            ) : (
              <Notice tone="caution">
                <p>{t('ui.flow.photo.none')}</p>
              </Notice>
            )}
          </div>
        </aside>

        <div className="review-list">
          {nothing ? (
            <Notice tone="caution">
              <p>{t('ui.flow.review.none_found')}</p>
            </Notice>
          ) : null}
          {data.medicines.map((m) => (
            <MedicineCard
              key={m.index}
              m={m}
              draft={drafts[m.index] ?? emptyDraft(m)}
              onChange={(d) => setDrafts((all) => ({ ...all, [m.index]: d }))}
              saved={saved?.[m.ref]}
              strengthAsLabel={data.strength_as_label_option}
              compareNote={data.compare_note}
            />
          ))}

          {added.map((a, k) => (
            <article key={a.key} className="med-card level-none">
              <header className="med-head">
                <h3 className="med-name">{a.formulary.generic}</h3>
                <span className="tag tag-accent"><Icon name="plus" size={16} /><span>{s('confirm.you_added', undefined, t('ui.flow.add.added'))}</span></span>
              </header>
              <p className="small">{[a.strength === data.strength_as_label_option ? s('picker.strength_as_label') : a.strength, a.dose, a.sched.times === 'as_needed' ? t('ui.flow.timing.as_needed') : a.sched.times, t(`ui.flow.timing.${a.sched.timing}`)].filter(Boolean).join(' · ')}</p>
              {saved?.[`a${k}`] ? <p className="saved-status"><Icon name="check" size={18} /><span>{t('ui.flow.review.saved_ok')}</span></p> : null}
              <Button variant="quiet" icon="close" onClick={() => setAdded((x) => x.filter((y) => y.key !== a.key))}>{t('ui.flow.add.remove')}</Button>
            </article>
          ))}

          {adding ? (
            <AddMedicine
              doseOptions={data.dose_options}
              strengthAsLabel={data.strength_as_label_option}
              compareNote={data.compare_note}
              onAdd={(a) => (setAdded((x) => [...x, a]), setAdding(false))}
              onCancel={() => setAdding(false)}
            />
          ) : (
            <div>
              <Button variant="secondary" icon="plus" onClick={() => setAdding(true)} disabled={added.length >= MAX_ADDED}>{t('ui.flow.add.open')}</Button>
              <p className="small muted">{t('ui.flow.add.hint')}</p>
            </div>
          )}
        </div>
      </div>

      <div className="summary-bar" role="region" aria-label={t('ui.flow.review.bar')}>
        <p className="summary-count" role="status">
          <Icon name={left ? 'circle-alert' : 'check'} size={20} />
          <span>{left ? t('ui.flow.review.left', { n: left }) : t('ui.flow.review.left_none')}</span>
          {dirty ? <span className="tag tag-draft">{t('ui.flow.review.unsaved')}</span> : null}
        </p>
        <Button icon="check" loading={saving} onClick={save} disabled={!dirty && !!saved}>{t('ui.flow.review.save')}</Button>
      </div>
      <div aria-live="assertive">{problem ? <ProblemNotice problem={problem} /> : null}</div>

      {saved ? (
        <div ref={savedRef} tabIndex={-1} className="saved-panel" role="status">
          <h2 className="h3-like">{t('ui.flow.review.saved_title')}</h2>
          <ul className="saved-list">
            {Object.values(saved).map((m) => {
              const med = data.medicines.find((x) => x.ref === m.ref)
              const a = m.ref.startsWith('a') ? added[Number(m.ref.slice(1))] : undefined
              const name = med ? med.as_written.brand || med.as_written.generic || t('ui.flow.review.no_name') : a?.formulary.generic
              return (
                <li key={m.ref}>
                  <strong>{name}</strong>
                  <span>
                    <Icon name={m.interaction_ready ? 'check' : 'circle-alert'} size={16} /> {m.interaction_ready ? t('ui.flow.saved.checked') : t('ui.flow.saved.not_checked')}
                  </span>
                  <span>
                    <Icon name={m.schedule_ready ? 'clock' : 'circle-alert'} size={16} /> {m.schedule_ready ? t('ui.flow.saved.scheduled') : t('ui.flow.saved.not_scheduled')}
                  </span>
                </li>
              )
            })}
          </ul>
          {data.medicines.some((m) => !saved[m.ref]) ? <p className="small muted">{t('ui.flow.saved.removed_note')}</p> : null}
        </div>
      ) : null}
      <div className="page-actions">
        <ButtonLink to={`/d/${id}/result`} icon="arrow" variant={saved && !dirty ? 'primary' : 'secondary'}>
          {t('ui.flow.review.see_results')}
        </ButtonLink>
      </div>

      <Dialog open={blocker.state === 'blocked'} onClose={() => blocker.state === 'blocked' && blocker.reset()} labelledBy="leave-title">
        <h2 id="leave-title" className="h3-like">{t('ui.flow.leave.title')}</h2>
        <p>{t('ui.flow.leave.body')}</p>
        <div className="page-actions">
          <Button autoFocus variant="primary" onClick={() => blocker.state === 'blocked' && blocker.reset()}>{t('ui.flow.leave.stay')}</Button>
          <Button variant="secondary" onClick={() => blocker.state === 'blocked' && blocker.proceed()}>{t('ui.flow.leave.go')}</Button>
        </div>
      </Dialog>
    </>
  )
}

