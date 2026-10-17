import { useEffect, useRef } from 'react'
import type { Problem } from '../api/errors'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { useServerStrings } from './serverStrings'

/** An error as text plus an icon (never colour alone). The backend's own message (GET /strings error.<code>) wins; client wording is the fallback.
 * It takes focus when it appears so the first error is announced after a failed submit. */
export function ProblemNotice({ problem, extra, id }: { problem: Problem; extra?: string; id?: string }) {
  const { t } = useT()
  const { s } = useServerStrings()
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => ref.current?.focus(), [problem])
  const backend = s(`error.${problem.code}`)
  const text = problem.kind === 'queue_full' && problem.retryAfter ? t('ui.flow.problem.queue_full_retry', { seconds: problem.retryAfter }) : backend || t(`ui.flow.problem.${problem.kind}`)
  return (
    <div ref={ref} id={id} tabIndex={-1} role="alert" className="field-error">
      <Icon name="alert" size={20} />
      <div>
        <p>{text}</p>
        {extra ? <p className="small">{extra}</p> : null}
      </div>
    </div>
  )
}
