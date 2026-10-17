import { useId } from 'react'
import { TIMING_LABELS } from '../../../api/openapi.generated'
import { TIMES_CHOICES, type SchedDraft } from '../../../flow/review'
import { useT } from '../../../i18n/I18n'

/** Times per day, timing label and duration, using the enums from the API (openapi.json). Pure form fields; the parent decides when they count. */
export function ScheduleFields({ value, onChange }: { value: SchedDraft; onChange: (v: SchedDraft) => void }) {
  const { t } = useT()
  const uid = useId()
  const set = (k: keyof SchedDraft) => (e: { target: { value: string } }) => onChange({ ...value, [k]: e.target.value })
  return (
    <div className="sched-fields">
      <div>
        <label htmlFor={`${uid}-t`} className="field-label">{t('ui.flow.sched.times')}</label>
        <select id={`${uid}-t`} value={value.times} onChange={set('times')}>
          <option value="">{t('ui.flow.sched.choose')}</option>
          {TIMES_CHOICES.map((c) => (
            <option key={c} value={c}>{c === 'as_needed' ? t('ui.flow.timing.as_needed') : c}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor={`${uid}-l`} className="field-label">{t('ui.flow.sched.timing')}</label>
        <select id={`${uid}-l`} value={value.timing} onChange={set('timing')}>
          {TIMING_LABELS.map((l) => (
            <option key={l} value={l}>{t(`ui.flow.timing.${l}`)}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor={`${uid}-d`} className="field-label">{t('ui.flow.sched.days')}</label>
        <input id={`${uid}-d`} type="number" inputMode="numeric" min={1} max={365} value={value.days} onChange={set('days')} aria-describedby={`${uid}-dh`} />
        <p id={`${uid}-dh`} className="small muted">{t('ui.flow.sched.days_hint')}</p>
      </div>
    </div>
  )
}
