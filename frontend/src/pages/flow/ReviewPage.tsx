import { useEffect, useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { useBlocker, useNavigate } from 'react-router-dom'
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
import { buildConfirmations, draftFromServer, emptyDraft, MAX_ADDED, orderMedicines, statusOf, type AddedDraft, type Draft } from '../../flow/review'
import { useServerStrings } from '../../flow/serverStrings'
import { DemoPhotoNote, PrerecordedNote } from '../../demo/DemoBar'
import { useDocId, useDocPath } from '../../demo/useDemo'
import { useT } from '../../i18n/I18n'
import { AddMedicine } from './review/AddMedicine'
import { MedicineCard } from './review/MedicineCard'
import { PhotoViewer } from './review/PhotoViewer'

export function ReviewPage() {
  const id = useDocId()
  return (
    <FlowPage titleKey="ui.title.review" narrow={false}>
      <Review id={id} />
    </FlowPage>
  )
}

const entryOrNull = (id: string | undefined | null) => (id ? getFormularyEntry(id).then((e) => e as FormularyEntry).catch(() => null) : Promise.resolve(null))

function Review({ id }: { id: string }) {
  const docPath = useDocPath()
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
  const [viewer, setViewer] = useState(false) // phones: the full-screen photo viewer
  const [open, setOpen] = useState<Record<number, boolean>>({}) // cards the person opened with Edit (a card that needs a check is always open)
  const [order, setOrder] = useState<'attention' | 'document'>('attention')
  const [barH, setBarH] = useState(80)
  const barRef = useRef<HTMLDivElement>(null)
  const lastJump = useRef<number | null>(null)
  const [imageTried, setImageTried] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const savedRef = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => {
    const el = barRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setBarH(el.offsetHeight))
    ro.observe(el)
    return () => ro.disconnect()
  }, [data])

  // load: the document must be waiting for confirmation, then the medicines (and any stored decisions, after a reload)
  useEffect(() => {
    if (!sessionLang) return
    const ctl = new AbortController()
    ;(async () => {
      try {
        const doc = await getDocument(id, ctl.signal)
        flow.upsertDoc(doc)
        if (doc.state !== 'awaiting_confirmation') {
          nav(docPath(id, 'processing'), { replace: true })
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

  const stat = (m: (typeof data.medicines)[number]) => statusOf(m, drafts[m.index], saved?.[m.ref])
  const ordered = orderMedicines(data.medicines, order)
  const attn = ordered.filter((m) => stat(m) === 'attention')
  const left = attn.length
  const checkedN = data.medicines.filter((m) => stat(m) === 'checked').length
  const nothing = data.medicines.length === 0 && added.length === 0

  const jump = () => {
    if (!attn.length) return
    const from = lastJump.current == null ? -1 : ordered.findIndex((m) => m.index === lastJump.current)
    const next = [...ordered.slice(from + 1), ...ordered.slice(0, from + 1)].find((m) => stat(m) === 'attention')
    if (!next) return
    lastJump.current = next.index
    const el = document.getElementById(`rv-h-${next.index}`)
    el?.scrollIntoView({ block: 'center' })
    el?.focus({ preventScroll: true })
  }
  const toggle = (i: number, now: boolean) => setOpen((o) => ({ ...o, [i]: !now }))
  const change = (index: number, d: Draft) => {
    const prev = drafts[index]
    setDrafts((all) => ({ ...all, [index]: d }))
    if (d.decided && !prev?.decided) {
      setOpen((o) => ({ ...o, [index]: false })) // a checked card folds away; the decision is kept
      requestAnimationFrame(() => document.getElementById(`rv-toggle-${index}`)?.focus())
    } else if (!d.decided && prev?.decided) setOpen((o) => ({ ...o, [index]: true })) // editing a checked card keeps it open
  }

  return (
    <>
      <SectionHeading as="h1" label={t('ui.flow.stage.check')} title={t('ui.flow.review.title')} />
      <p className="lede">{t('ui.flow.review.intro')}</p>
      <div className="review-shell" style={{ '--bar-h': `${barH}px` } as CSSProperties} lang={lang}>
        <div ref={barRef} className="summary-bar rv-bar" role="region" aria-label={t('ui.flow.review.bar')}>
          <p className="rv-counts" role="status" aria-live="polite" aria-atomic="true">
            <span>
              <Icon name="check" size={20} />
              <span>{t('ui.flow.rv.progress', { n: checkedN, m: data.medicines.length })}</span>
            </span>
            <span>
              <Icon name={left ? 'circle-alert' : 'check'} size={20} />
              <span>{left ? t('ui.flow.rv.attention', { n: left }) : t('ui.flow.review.left_none')}</span>
            </span>
            {dirty ? <span className="tag tag-draft">{t('ui.flow.review.unsaved')}</span> : null}
          </p>
          <div className="rv-actions">
            <button type="button" className="jump-btn" disabled={!left} onClick={jump}>
              <Icon name="chevron" size={18} />
              <span>{t('ui.flow.rv.jump')}</span>
            </button>
            <Button icon="check" loading={saving} onClick={save} disabled={!dirty && !!saved}>{t('ui.flow.review.save')}</Button>
          </div>
        </div>

        <div className="review-grid">
          <aside className="rv-pane" aria-label={t('ui.flow.photo.label')}>
            <DemoPhotoNote />
            {photoUrl ? (
              <PhotoViewer url={photoUrl} />
            ) : (
              <Notice tone="caution">
                <p>{t('ui.flow.photo.none')}</p>
              </Notice>
            )}
          </aside>

          <div className="review-list">
            <Notice tone="important" title={t('ui.flow.review.meaning.title')}>
              <p>{t('ui.flow.review.meaning')}</p>
              <p>{t('ui.flow.review.risk')}</p>
            </Notice>
            <div className="phone-photo">
              <DemoPhotoNote />
              {photoUrl ? (
                <>
                  <button type="button" className="rv-thumb" aria-label={t('ui.flow.photo.show')} onClick={() => setViewer(true)}>
                    <img src={photoUrl} alt="" />
                  </button>
                  <button type="button" onClick={() => setViewer(true)}>
                    <Icon name="zoomin" size={20} />
                    <span>{t('ui.flow.photo.show')}</span>
                  </button>
                </>
              ) : (
                <Notice tone="caution">
                  <p>{t('ui.flow.photo.none')}</p>
                </Notice>
              )}
            </div>
            {nothing ? (
              <Notice tone="caution">
                <p>{t('ui.flow.review.none_found')}</p>
              </Notice>
            ) : null}
            {data.medicines.length > 1 ? (
              <div className="rv-listhead">
                <h2 className="h3-like">{t('ui.flow.rv.list_label')}</h2>
                <button type="button" className="order-btn" onClick={() => setOrder(order === 'attention' ? 'document' : 'attention')}>
                  <Icon name="reset" size={18} />
                  <span>{order === 'attention' ? t('ui.flow.rv.order.doc') : t('ui.flow.rv.order.attention')}</span>
                </button>
              </div>
            ) : null}
            {ordered.map((m) => {
              const st = stat(m)
              return (
                <MedicineCard
                  key={m.index}
                  m={m}
                  draft={drafts[m.index] ?? emptyDraft(m)}
                  onChange={(d) => change(m.index, d)}
                  saved={saved?.[m.ref]}
                  strengthAsLabel={data.strength_as_label_option}
                  compareNote={data.compare_note}
                  status={st}
                  expanded={st === 'attention' || open[m.index] === true}
                  onToggle={() => toggle(m.index, st === 'attention' || open[m.index] === true)}
                />
              )
            })}

            {added.map((a, k) => (
              <article key={a.key} className="med-card level-none status-checked">
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
      </div>

      <Dialog open={viewer} onClose={() => setViewer(false)} labelledBy="viewer-title" className="dialog-full">
        <div className="dialog-bar">
          <h2 id="viewer-title">{t('ui.flow.photo.label')}</h2>
          <Button variant="secondary" icon="close" autoFocus onClick={() => setViewer(false)}>{t('ui.flow.rv.viewer_close')}</Button>
        </div>
        {photoUrl ? <PhotoViewer url={photoUrl} /> : null}
      </Dialog>
      <div aria-live="assertive">{problem ? <ProblemNotice problem={problem} /> : null}</div>

      {saved ? (
        <div ref={savedRef} tabIndex={-1} className="saved-panel" role="status">
          <h2 className="h3-like">{t('ui.flow.review.saved_title')}</h2>
          <PrerecordedNote />
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
        <ButtonLink to={docPath(id, 'result')} icon="arrow" variant={saved && !dirty ? 'primary' : 'secondary'}>
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

