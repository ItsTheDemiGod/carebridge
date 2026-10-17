import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getDocument, retryDocument } from '../../api/endpoints'
import { isAbort, toProblem, type Problem } from '../../api/errors'
import { startPolling } from '../../api/poll'
import type { DocView } from '../../api/types'
import { useProcessingScreen } from '../../ambient/motion'
import { Button, ButtonLink } from '../../components/Button'
import { Notice } from '../../components/Badges'
import { Icon } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { ProblemNotice } from '../../flow/ProblemNotice'
import { useServerStrings } from '../../flow/serverStrings'
import { docById } from '../../flow/state'
import { useT } from '../../i18n/I18n'

const STAGES = ['queued', 'extracting', 'normalising'] as const

export function ProcessingPage() {
  const { id = '' } = useParams()
  return (
    <FlowPage titleKey="ui.title.processing">
      <Processing id={id} />
    </FlowPage>
  )
}

function Processing({ id }: { id: string }) {
  const { t } = useT()
  const { s } = useServerStrings()
  const flow = useFlow()
  const nav = useNavigate()
  useProcessingScreen() // the ambient particle layer stays paused here (GPU is busy with the model)
  const doc: DocView | undefined = docById(flow.state, id)
  const [problem, setProblem] = useState<Problem | null>(null)
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState(false)
  const [round, setRound] = useState(0) // bumped by retry to restart the polling
  const state = doc?.state
  const finished = state === 'awaiting_confirmation' || state === 'failed'

  useEffect(() => {
    if (finished) return
    return startPolling({
      fetch: (signal) => getDocument(id, signal),
      isDone: (d) => d.state === 'awaiting_confirmation' || d.state === 'failed',
      onValue: (d) => {
        setOffline(false)
        flow.upsertDoc(d)
      },
      onError: (e) => {
        if (isAbort(e)) return false
        const p = toProblem(e)
        if (p.kind === 'network' || p.kind === 'server') {
          setOffline(true)
          return true
        }
        setProblem(flow.report(e))
        return false
      },
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, round, finished])

  useEffect(() => {
    if (state === 'awaiting_confirmation') nav(`/d/${id}/review`, { replace: true })
  }, [state, id, nav])

  const retry = async () => {
    setBusy(true)
    setProblem(null)
    try {
      flow.upsertDoc(await retryDocument(id))
      setRound((n) => n + 1)
    } catch (e) {
      setProblem(flow.report(e))
    }
    setBusy(false)
  }

  if (problem && !doc) {
    return (
      <>
        <SectionHeading as="h1" label={t('ui.flow.stage.photo')} title={t('ui.flow.processing.title')} />
        <ProblemNotice problem={problem} />
        <div className="page-actions">
          <ButtonLink to="/upload" icon="arrow">{t('ui.flow.processing.upload_again')}</ButtonLink>
          <ButtonLink to="/start" variant="quiet">{t('ui.flow.processing.to_start')}</ButtonLink>
        </div>
      </>
    )
  }

  const at = state ? Math.max(0, STAGES.indexOf(state as (typeof STAGES)[number])) : 0
  const failed = state === 'failed' || state === 'expired' || state === 'deleted'

  return (
    <>
      <SectionHeading as="h1" label={t('ui.flow.stage.photo')} title={failed ? t('ui.flow.processing.failed_title') : t('ui.flow.processing.title')} />
      {failed ? (
        <>
          <Notice tone="important" title={t('ui.flow.processing.failed_title')}>
            <p>{doc?.error_message || s(`job.failed.${doc?.error_code}`) || t('ui.flow.problem.unknown')}</p>
          </Notice>
          {problem ? <ProblemNotice problem={problem} /> : null}
          <p className="muted">{doc?.retry_possible ? t('ui.flow.processing.kept_hint') : t('ui.flow.processing.not_kept_hint')}</p>
          <div className="page-actions">
            {doc?.retry_possible ? (
              <Button icon="arrow" loading={busy} onClick={retry}>
                {t('ui.flow.processing.retry')}
              </Button>
            ) : null}
            <ButtonLink to="/upload" variant={doc?.retry_possible ? 'secondary' : 'primary'} icon="camera">
              {t('ui.flow.processing.upload_again')}
            </ButtonLink>
            <ButtonLink to="/start" variant="quiet">
              {t('ui.flow.processing.to_start')}
            </ButtonLink>
          </div>
        </>
      ) : (
        <>
          <p className="lede">{t('ui.flow.processing.estimate')}</p>
          <div className="busy-bar" role="progressbar" aria-label={t('ui.flow.processing.title')} aria-valuetext={t(`ui.flow.processing.stage.${STAGES[at]}`)}>
            <span />
          </div>
          <ol className="stage-list">
            {STAGES.map((st, i) => (
              <li key={st} aria-current={i === at ? 'step' : undefined} className={i < at ? 'done' : i === at ? 'now' : ''}>
                <Icon name={i < at ? 'check' : i === at ? 'clock' : 'leaf'} size={22} />
                <span>{t(`ui.flow.processing.stage.${st}`)}</span>
                <span className="sr-only">{i < at ? t('ui.flow.progress.done') : ''}</span>
              </li>
            ))}
          </ol>
          <p className="muted">{t('ui.flow.processing.nothing_to_do')}</p>
          <div className="sr-only" role="status" aria-live="polite">
            {t(`ui.flow.processing.stage.${STAGES[at]}`)}
          </div>
          {offline ? (
            <Notice tone="caution">
              <p>{t('ui.flow.processing.offline')}</p>
            </Notice>
          ) : null}
          {problem ? <ProblemNotice problem={problem} /> : null}
        </>
      )}
    </>
  )
}
