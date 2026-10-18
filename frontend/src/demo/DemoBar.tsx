import { Link } from 'react-router-dom'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { useIsDemo } from './useDemo'

/** The persistent label on every sample page: what this is, what it does not do, and the way out. */
export function DemoBar() {
  const { t } = useT()
  return (
    <aside className="demo-bar" aria-label={t('ui.demo.tag')}>
      <p className="demo-bar-label">
        <Icon name="info" size={20} />
        <span>{t('ui.demo.label')}</span>
      </p>
      <p className="demo-bar-sub muted">{t('ui.demo.nothing_to_delete')}</p>
      <Link className="text-link demo-leave" to="/">
        {t('ui.demo.leave')}
      </Link>
    </aside>
  )
}

/** After Save in the sample the result is the recorded one, whatever was chosen. Renders nothing outside the sample. */
export function PrerecordedNote() {
  const { t } = useT()
  if (!useIsDemo()) return null
  return (
    <p className="demo-note" role="note">
      <Icon name="info" size={18} />
      <span>{t('ui.demo.prerecorded_note')}</span>
    </p>
  )
}

/** Schedule page of the sample: marks are kept in memory only. */
export function DemoMarksNote() {
  const { t } = useT()
  if (!useIsDemo()) return null
  return <p className="muted">{t('ui.demo.marks_note')}</p>
}

/** Shown beside the "service not reachable" message: the sample needs no connection. */
export function SampleLink() {
  const { t } = useT()
  return (
    <p className="sample-link">
      {t('ui.demo.unreachable')} <Link className="text-link" to="/demo">{t('ui.demo.try')}</Link>
    </p>
  )
}

/** A quiet entry point to the sample (start page, how it works). */
export function TrySampleLink() {
  const { t } = useT()
  return (
    <p className="sample-link">
      <Link className="text-link" to="/demo">{t('ui.demo.try')}</Link>
    </p>
  )
}
