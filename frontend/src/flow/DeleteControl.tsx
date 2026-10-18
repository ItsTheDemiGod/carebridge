import { useId, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'
import { Dialog } from '../components/Dialog'
import { Icon } from '../components/icons'
import { useT } from '../i18n/I18n'
import { useIsDemo } from '../demo/useDemo'
import { useFlow } from './FlowProvider'

/** "Delete my data": shown in the header once a session exists. Withdrawing consent is the same action. */
export function DeleteControl({ labelKey = 'ui.flow.delete.button', className = 'delete-btn' }: { labelKey?: string; className?: string } = {}) {
  const { t } = useT()
  const flow = useFlow()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)
  const tid = useId()
  const demo = useIsDemo()
  if (!flow.state.session || demo) return null // nothing is stored in the sample (the demo bar says so)

  const run = async () => {
    setBusy(true)
    setFailed(false)
    const receipt = await flow.deleteAll()
    setBusy(false)
    if (receipt) {
      setOpen(false)
      nav('/')
    } else setFailed(true)
  }
  return (
    <>
      <button type="button" className={className} title={t(labelKey)} onClick={() => setOpen(true)}>
        <Icon name="trash" size={20} />
        <span>{t(labelKey)}</span>
      </button>
      <Dialog open={open} onClose={() => !busy && setOpen(false)} labelledBy={tid}>
        <h2 id={tid} className="h3-like">
          {t('ui.flow.delete.title')}
        </h2>
        <p>{t('ui.flow.delete.body')}</p>
        <ul className="plain-list">
          <li>{t('ui.flow.delete.c1')}</li>
          <li>{t('ui.flow.delete.c2')}</li>
          <li>{t('ui.flow.delete.c3')}</li>
        </ul>
        {failed ? (
          <p role="alert" className="field-error">
            <Icon name="alert" size={18} /> <span>{t('ui.flow.delete.failed')}</span>
          </p>
        ) : null}
        <div className="page-actions">
          <Button variant="secondary" autoFocus onClick={() => setOpen(false)} disabled={busy}>
            {t('ui.flow.delete.cancel')}
          </Button>
          <Button variant="primary" icon="trash" loading={busy} onClick={run} className="btn-danger">
            {t('ui.flow.delete.confirm')}
          </Button>
        </div>
      </Dialog>
    </>
  )
}
