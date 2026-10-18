import { Link } from 'react-router-dom'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { useIsDemo } from './useDemo'

/** The persistent label of the sample: part of the sticky header, so it stays on screen while the page scrolls. What this is, what it does not do, the way out. */
export function DemoStrip() {
  const { t } = useT()
  return (
    <div className="container demo-strip" role="note">
      <p className="demo-strip-label">
        <Icon name="info" size={18} />
        <span>{t('ui.demo.label')}</span>
      </p>
      <Link className="text-link demo-leave" to="/">
        {t('ui.demo.leave')}
      </Link>
    </div>
  )
}

/** Top of every sample page: there is nothing to delete here. */
export function DemoBar() {
  const { t } = useT()
  return <p className="demo-bar muted">{t('ui.demo.nothing_to_delete')}</p>
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

/** Review page of the sample: says why the photo looks poor, above the photo viewer. */
export function DemoPhotoNote() {
  const { t } = useT()
  if (!useIsDemo()) return null
  return <p className="demo-photo-note small">{t('ui.demo.photo_note')}</p>
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
