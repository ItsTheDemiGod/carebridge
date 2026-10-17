import { useId } from 'react'
import type { ConfirmedSummary, FormularyEntry, MedicineAction, ReviewMedicine } from '../../../api/types'
import { Button } from '../../../components/Button'
import { Icon } from '../../../components/icons'
import { ackReasons, isNonDaily, isTiming, missing, NOTE_MAX, nameReasons, type Draft } from '../../../flow/review'
import { fill, useServerStrings } from '../../../flow/serverStrings'
import { useT } from '../../../i18n/I18n'
import { FormularyPicker } from './FormularyPicker'
import { ScheduleFields } from './ScheduleFields'

const LEVEL_ICON = { must_confirm: 'alert', note: 'info', none: 'check' } as const

export function ReviewBadge({ level }: { level: ReviewMedicine['review_level'] }) {
  const { t } = useT()
  return (
    <span className={`review-badge rb-${level}`}>
      <Icon name={LEVEL_ICON[level]} size={16} />
      <span>{t(`ui.flow.review.level.${level}`)}</span>
    </span>
  )
}

type Props = {
  m: ReviewMedicine
  draft: Draft
  onChange: (d: Draft) => void
  saved?: ConfirmedSummary
  strengthAsLabel: string
  compareNote: string
}

export function MedicineCard({ m, draft, onChange, saved, strengthAsLabel, compareNote }: Props) {
  const { t } = useT()
  const { s } = useServerStrings()
  const uid = useId()
  const set = (p: Partial<Draft>) => onChange({ ...draft, ...p })
  const name = m.as_written.brand || m.as_written.generic || t('ui.flow.review.no_name')
  const need = missing(m, draft)
  const nonDaily = isNonDaily(m)
  const acks = ackReasons(m)
  const names = nameReasons(m)
  const actions = m.allowed_actions
  const idle = !m.has_exact_identity && names.length > 0
  const pick = (e: FormularyEntry) => set({ formulary: e, strength: null })
  const chooseAction = (a: MedicineAction) => set({ action: a, decided: false })
  const decided = draft.decided && need.length === 0

  return (
    <article className={`med-card level-${m.review_level}`} aria-labelledby={`${uid}-h`}>
      <header className="med-head">
        <h3 id={`${uid}-h`} className="med-name">{name}</h3>
        <ReviewBadge level={m.review_level} />
        {decided ? (
          <span className="tag tag-accent"><Icon name="check" size={16} /><span>{t('ui.flow.review.decided')}</span></span>
        ) : null}
      </header>

      <figure className="quote">
        <figcaption className="label">{t('ui.flow.review.quote')}</figcaption>
        <blockquote>{m.source_quote ?? t('ui.flow.review.no_quote')}</blockquote>
      </figure>
      <dl className="facts">
        <div><dt>{t('ui.flow.review.f.strength')}</dt><dd>{m.strength ?? '—'}</dd></div>
        <div><dt>{t('ui.flow.review.f.dose')}</dt><dd>{m.dose ?? '—'}</dd></div>
        <div>
          <dt>{t('ui.flow.review.f.frequency')}</dt>
          <dd>{[m.frequency.original_abbreviation, m.frequency.times_per_day != null ? String(m.frequency.times_per_day) : null, isTiming(m.frequency.timing_label) ? t(`ui.flow.timing.${m.frequency.timing_label}`) : m.frequency.timing_label].filter(Boolean).join(' · ') || '—'}</dd>
        </div>
        <div><dt>{t('ui.flow.review.f.duration')}</dt><dd>{m.duration_text ?? (m.duration_days != null ? String(m.duration_days) : '—')}</dd></div>
      </dl>

      {m.reasons.length ? (
        <div className="reasons">
          <p className="label">{t('ui.flow.review.reasons')}</p>
          <ul>
            {m.reasons.map((r) => (
              <li key={r.id}>
                <Icon name={r.kind === 'name' ? 'search' : 'circle-alert'} size={18} />
                <span>{r.text ?? t('ui.flow.review.reason_generic')}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {nonDaily ? (
        <p className="inline-note"><Icon name="calendar" size={18} /><span>{s('schedule.not.non_daily', undefined, t('ui.flow.review.non_daily'))}</span></p>
      ) : null}

      {saved ? (
        <p className="saved-status" role="status">
          <Icon name={saved.review_level === 'must_confirm' || saved.unresolved.length ? 'circle-alert' : 'check'} size={18} />
          <span>
            {saved.unresolved.length || saved.review_level === 'must_confirm' ? t('ui.flow.review.saved_open') : t('ui.flow.review.saved_ok')}{' '}
            {saved.not_checked_reason ? s(`confirm.flag.${saved.not_checked_reason}`) : ''}
          </span>
        </p>
      ) : null}

      <fieldset className="actions" disabled={false}>
        <legend className="label">{t('ui.flow.review.what_is_right')}</legend>
        {actions.map((a) => (
          <div key={a} className="check-row radio">
            <input type="radio" id={`${uid}-${a}`} name={`${uid}-action`} checked={draft.action === a} onChange={() => chooseAction(a)} />
            <label htmlFor={`${uid}-${a}`}>{s(`confirm.action.${a}`, undefined, a)}</label>
          </div>
        ))}
      </fieldset>

      {draft.action === 'confirm_as_extracted' && idle ? (
        <p className="inline-note"><Icon name="info" size={18} /><span>{t('ui.flow.review.unidentified_note')}</span></p>
      ) : null}

      {draft.action === 'select_formulary_drug' ? (
        <div className="panel">
          <p className="small">{compareNote}</p>
          {draft.formulary ? (
            <div className="picked">
              <p><strong>{draft.formulary.generic}</strong></p>
              <p className="small">{s('picker.brand', undefined, '')}: {draft.formulary.brand_names.join(', ')}</p>
              <Button variant="quiet" onClick={() => set({ formulary: null, strength: null })}>{t('ui.flow.review.change_drug')}</Button>
              <fieldset className="strengths">
                <legend className="label">{s('picker.strength', undefined, t('ui.flow.picker.strength'))}</legend>
                {[...draft.formulary.available_strengths, strengthAsLabel].map((st) => (
                  <div key={st} className="check-row radio">
                    <input type="radio" id={`${uid}-st-${st}`} name={`${uid}-st`} checked={draft.strength === st} onChange={() => set({ strength: st })} />
                    <label htmlFor={`${uid}-st-${st}`}>{st === strengthAsLabel ? s('picker.strength_as_label', undefined, st) : st}</label>
                  </div>
                ))}
              </fieldset>
            </div>
          ) : (
            <FormularyPicker onPick={pick} />
          )}
        </div>
      ) : null}

      {draft.action === 'not_in_list' ? (
        <div className="panel">
          <label htmlFor={`${uid}-note`} className="field-label">{s('confirm.note_label', undefined, t('ui.flow.review.note'))}</label>
          <input id={`${uid}-note`} type="text" maxLength={NOTE_MAX} value={draft.note} onChange={(e) => set({ note: e.target.value, decided: false })} aria-describedby={`${uid}-nh`} />
          <p id={`${uid}-nh`} className="small muted">{fill(t('ui.flow.review.note_count'), { n: draft.note.length, max: NOTE_MAX })} {t('ui.flow.review.note_hint')}</p>
        </div>
      ) : null}

      {draft.action === 'remove' ? <p className="inline-note"><Icon name="info" size={18} /><span>{t('ui.flow.review.remove_note')}</span></p> : null}

      {(draft.action === 'confirm_as_extracted' || draft.action === 'select_formulary_drug') && acks.length ? (
        <fieldset className="panel acks">
          <legend className="label">{t('ui.flow.review.acks')}</legend>
          {acks.map((r) => (
            <div key={r.id} className="check-row">
              <input
                type="checkbox"
                id={`${uid}-ack-${r.id}`}
                checked={draft.acks.includes(r.id)}
                onChange={(e) => set({ acks: e.target.checked ? [...draft.acks, r.id] : draft.acks.filter((x) => x !== r.id), decided: false })}
              />
              <label htmlFor={`${uid}-ack-${r.id}`}>{r.text ?? t('ui.flow.review.ack_generic')}</label>
            </div>
          ))}
        </fieldset>
      ) : null}

      {(draft.action === 'confirm_as_extracted' || draft.action === 'select_formulary_drug') && !nonDaily ? (
        <details className="panel sched" open={draft.schedTouched}>
          <summary>{t('ui.flow.review.sched_edit')}</summary>
          <p className="small muted">{t('ui.flow.review.sched_hint')}</p>
          <ScheduleFields value={draft.sched} onChange={(v) => set({ sched: v, schedTouched: true, decided: false })} />
        </details>
      ) : null}

      {draft.action ? (
        <div className="card-confirm">
          <Button
            icon="check"
            disabled={need.length > 0 || decided}
            aria-describedby={need.length ? `${uid}-need` : undefined}
            onClick={() => set({ decided: true })}
          >
            {draft.action === 'remove' ? t('ui.flow.review.btn_remove') : draft.action === 'not_in_list' ? t('ui.flow.review.btn_not_in_list') : t('ui.flow.review.btn_confirm')}
          </Button>
          {need.length ? (
            <p id={`${uid}-need`} className="small muted">
              {t('ui.flow.review.still_needed')} {need.map((k) => t(`ui.flow.review.needs.${k}`)).join(', ')}
            </p>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}
