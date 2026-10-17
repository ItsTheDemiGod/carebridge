import { useLocation } from 'react-router-dom'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { STAGES, stageForPath } from './state'

/** Header of flow pages: consent, photo, check, results, schedule. Current step by text + shape + aria-current, never colour alone. */
export function Progress() {
  const { t } = useT()
  const stage = stageForPath(useLocation().pathname)
  if (!stage) return null
  const at = STAGES.indexOf(stage)
  return (
    <nav className="flow-progress" aria-label={t('ui.flow.progress.label')}>
      <ol>
        {STAGES.map((s, i) => (
          <li key={s} aria-current={i === at ? 'step' : undefined} className={i < at ? 'done' : i === at ? 'now' : ''}>
            <span className="fp-mark" aria-hidden="true">
              {i < at ? <Icon name="check" size={14} /> : i + 1}
            </span>
            <span>{t(`ui.flow.stage.${s}`)}</span>
            {i < at ? <span className="sr-only">{t('ui.flow.progress.done')}</span> : null}
          </li>
        ))}
      </ol>
    </nav>
  )
}
