import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadDocument } from '../../api/endpoints'
import type { Problem } from '../../api/errors'
import { Button } from '../../components/Button'
import { Notice } from '../../components/Badges'
import { Icon } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { useT } from '../../i18n/I18n'
import { checkFile } from '../../lib/sniff'

const synthetic = (kind: Problem['kind'], code: string): Problem => ({ kind, code, status: 0, retryAfter: null })

export function UploadPage() {
  const { t } = useT()
  const flow = useFlow()
  const nav = useNavigate()
  const pending = useRef<{ blob: Blob; type: string } | null>(null) // the chosen file, in memory only
  const [hasPhoto, setHasPhoto] = useState(false)
  const [problem, setProblem] = useState<Problem | null>(null)
  const [busy, setBusy] = useState(false)
  const [over, setOver] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const maxBytes = flow.state.session?.limits.max_upload_bytes ?? 10_000_000

  const choose = async (file: File | undefined | null) => {
    if (!file) return
    setProblem(null)
    const c = await checkFile(file, maxBytes)
    if (!c.ok) {
      pending.current = null
      flow.setPhoto(null)
      setHasPhoto(false)
      setProblem(c.reason === 'pdf' ? synthetic('pdf', 'pdf_not_supported') : c.reason === 'too_large' ? synthetic('too_large', 'upload_too_large') : synthetic('unsupported', 'unsupported_file'))
      return
    }
    pending.current = { blob: file, type: c.type }
    flow.setPhoto(file)
    setHasPhoto(true)
  }

  const reset = () => {
    pending.current = null
    flow.setPhoto(null)
    setHasPhoto(false)
    setProblem(null)
    fileInput.current?.focus()
  }

  const use = async () => {
    const p = pending.current
    if (!p || busy) return
    setBusy(true)
    setProblem(null)
    try {
      const doc = await uploadDocument(p.blob, p.type)
      pending.current = null // sent once; never sent twice, never stored
      flow.upsertDoc(doc)
      nav(`/d/${doc.id}/processing`)
    } catch (e) {
      setProblem(flow.report(e))
      setBusy(false)
    }
  }

  return (
    <FlowPage titleKey="ui.title.upload">
      <SectionHeading as="h1" label={t('ui.flow.stage.photo')} title={t('ui.flow.upload.title')} />
      <p className="lede">{t('ui.flow.upload.intro')}</p>

      {!hasPhoto ? (
        <>
          <div
            className={`dropzone${over ? ' over' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setOver(true)
            }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => {
              e.preventDefault()
              setOver(false)
              void choose(e.dataTransfer.files[0])
            }}
          >
            <Icon name="document" size={40} />
            <p>{t('ui.flow.upload.drop')}</p>
            <div className="page-actions">
              <input ref={fileInput} id="file-pick" className="sr-only" type="file" accept="image/png,image/jpeg" onChange={(e) => void choose(e.target.files?.[0])} />
              <label htmlFor="file-pick" className="btn btn-primary">
                <span>{t('ui.flow.upload.pick')}</span>
              </label>
              <input id="file-camera" className="sr-only" type="file" accept="image/png,image/jpeg" capture="environment" onChange={(e) => void choose(e.target.files?.[0])} />
              <label htmlFor="file-camera" className="btn btn-secondary">
                <Icon name="camera" size={20} />
                <span>{t('ui.flow.upload.camera')}</span>
              </label>
            </div>
            <p className="small muted">{t('ui.flow.upload.types')}</p>
          </div>
        </>
      ) : (
        <figure className="preview">
          {flow.state.photoUrl ? <img src={flow.state.photoUrl} alt={t('ui.flow.upload.preview_alt')} /> : null}
          <figcaption className="small muted">{t('ui.flow.upload.preview_note')}</figcaption>
          <div className="page-actions">
            <Button icon="arrow" loading={busy} onClick={use}>
              {t('ui.flow.upload.use')}
            </Button>
            <Button variant="secondary" disabled={busy} onClick={reset}>
              {t('ui.flow.upload.another')}
            </Button>
          </div>
        </figure>
      )}
      <div aria-live="assertive">{problem ? <ProblemNotice problem={problem} /> : null}</div>

      <Notice tone="info" title={t('ui.flow.upload.guide.title')}>
        <ul className="plain-list">
          <li>{t('ui.flow.upload.guide.1')}</li>
          <li>{t('ui.flow.upload.guide.2')}</li>
          <li>{t('ui.flow.upload.guide.3')}</li>
          <li>{t('ui.flow.upload.guide.4')}</li>
        </ul>
        <p>{t('ui.flow.upload.local')}</p>
      </Notice>
    </FlowPage>
  )
}
