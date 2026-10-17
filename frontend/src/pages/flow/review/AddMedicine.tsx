import { useId, useState } from 'react'
import type { FormularyEntry } from '../../../api/types'
import { Button } from '../../../components/Button'
import { addedReady, type AddedDraft, type SchedDraft } from '../../../flow/review'
import { useServerStrings } from '../../../flow/serverStrings'
import { useT } from '../../../i18n/I18n'
import { FormularyPicker } from './FormularyPicker'
import { ScheduleFields } from './ScheduleFields'

const BLANK: SchedDraft = { times: '', timing: 'unspecified', days: '' }

/** "Add a medicine I do not see here": only the formulary picker (no free text), a fixed dose list from the API, and a schedule. */
export function AddMedicine({ doseOptions, strengthAsLabel, compareNote, onAdd, onCancel }: { doseOptions: string[]; strengthAsLabel: string; compareNote: string; onAdd: (a: AddedDraft) => void; onCancel: () => void }) {
  const { t } = useT()
  const { s } = useServerStrings()
  const uid = useId()
  const [entry, setEntry] = useState<FormularyEntry | null>(null)
  const [strength, setStrength] = useState<string | null>(null)
  const [dose, setDose] = useState('')
  const [sched, setSched] = useState<SchedDraft>(BLANK)
  const ready = addedReady({ formulary: entry ?? undefined, strength: strength ?? undefined, dose, sched })
  return (
    <section className="panel add-med" aria-labelledby={`${uid}-h`}>
      <h3 id={`${uid}-h`} className="h3-like">{t('ui.flow.add.title')}</h3>
      <p className="small">{compareNote}</p>
      {entry ? (
        <div className="picked">
          <p><strong>{entry.generic}</strong></p>
          <p className="small">{s('picker.brand', undefined, '')}: {entry.brand_names.join(', ')}</p>
          <Button variant="quiet" onClick={() => (setEntry(null), setStrength(null))}>{t('ui.flow.review.change_drug')}</Button>
          <fieldset className="strengths">
            <legend className="label">{s('picker.strength', undefined, t('ui.flow.picker.strength'))}</legend>
            {[...entry.available_strengths, strengthAsLabel].map((st) => (
              <div key={st} className="check-row radio">
                <input type="radio" id={`${uid}-st-${st}`} name={`${uid}-st`} checked={strength === st} onChange={() => setStrength(st)} />
                <label htmlFor={`${uid}-st-${st}`}>{st === strengthAsLabel ? s('picker.strength_as_label', undefined, st) : st}</label>
              </div>
            ))}
          </fieldset>
        </div>
      ) : (
        <FormularyPicker onPick={setEntry} />
      )}
      <div>
        <label htmlFor={`${uid}-dose`} className="field-label">{t('ui.flow.add.dose')}</label>
        <select id={`${uid}-dose`} value={dose} onChange={(e) => setDose(e.target.value)}>
          <option value="">{t('ui.flow.sched.choose')}</option>
          {doseOptions.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>
      <ScheduleFields value={sched} onChange={setSched} />
      <div className="page-actions">
        <Button icon="plus" disabled={!ready} onClick={() => onAdd({ key: `${Date.now()}-${Math.random()}`, formulary: entry!, strength: strength!, dose, sched })}>
          {t('ui.flow.add.confirm')}
        </Button>
        <Button variant="quiet" onClick={onCancel}>{t('ui.flow.add.cancel')}</Button>
      </div>
      {!ready ? <p className="small muted">{t('ui.flow.add.needs')}</p> : null}
    </section>
  )
}
