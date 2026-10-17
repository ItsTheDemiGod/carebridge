import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ButtonLink } from '../../components/Button'
import { Notice, Tag } from '../../components/Badges'
import { Icon, type IconName } from '../../components/icons'
import { SectionHeading } from '../../components/Layout'
import { DeleteControl } from '../../flow/DeleteControl'
import { FlowPage } from '../../flow/FlowPage'
import { useFlow } from '../../flow/FlowProvider'
import { routeForDoc } from '../../flow/state'
import { useT } from '../../i18n/I18n'

/** every state is icon + words (a different icon per kind of state) */
const STATE_ICON: Record<string, IconName> = { queued: 'clock', extracting: 'clock', normalising: 'clock', awaiting_confirmation: 'circle-alert', failed: 'alert', expired: 'close', deleted: 'close' }

export function DocumentsPage() {
  const { t, lang } = useT()
  const flow = useFlow()
  const { refreshDocs } = flow
  const ready = flow.state.boot === 'ready'
  useEffect(() => {
    if (ready) void refreshDocs()
  }, [ready, refreshDocs])
  const fmt = (iso: string) => new Date(iso).toLocaleString(lang === 'en' ? 'en-IN' : lang === 'ta' ? 'ta-IN' : 'hi-IN', { dateStyle: 'medium', timeStyle: 'short' })
  return (
    <FlowPage titleKey="ui.title.documents">
      <SectionHeading as="h1" label={t('ui.flow.nav.documents')} title={t('ui.flow.docs.title')} />
      <p className="lede">{t('ui.flow.docs.intro')}</p>
      {flow.state.docs.length === 0 ? (
        <p className="muted lede-icon"><Icon name="document" size={28} /><span>{t('ui.flow.docs.empty')}</span></p>
      ) : (
        <ul className="res-lines">
          {flow.state.docs.map((d) => (
            <li key={d.id} className="res-line">
              <p className="line-text"><strong>{fmt(d.created_at)}</strong><Tag tone={d.state === 'failed' ? 'neutral' : 'accent'} icon={STATE_ICON[d.state] ?? 'info'}>{t(`ui.flow.docs.state.${d.state}`)}</Tag></p>
              <p>
                <Link className="text-link" to={routeForDoc(d)}>{d.state === 'awaiting_confirmation' ? t('ui.flow.docs.open_review') : t('ui.flow.docs.open')}</Link>
                {d.state === 'awaiting_confirmation' ? <> · <Link className="text-link" to={`/d/${d.id}/result`}>{t('ui.flow.docs.open_result')}</Link></> : null}
              </p>
            </li>
          ))}
        </ul>
      )}
      <Notice tone="important" title={t('ui.flow.docs.delete.title')}>
        <p>{t('ui.flow.docs.delete.body')}</p>
        <div className="page-actions"><DeleteControl labelKey="ui.flow.docs.delete.button" /></div>
      </Notice>
      <div className="page-actions"><ButtonLink to="/upload" icon="camera">{t('ui.flow.docs.new')}</ButtonLink></div>
    </FlowPage>
  )
}
