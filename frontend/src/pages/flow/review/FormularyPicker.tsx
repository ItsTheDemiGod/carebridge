import { useEffect, useId, useRef, useState } from 'react'
import { searchFormulary } from '../../../api/endpoints'
import { isAbort, toProblem, type Problem } from '../../../api/errors'
import type { FormularyEntry } from '../../../api/types'
import { Icon } from '../../../components/icons'
import { ProblemNotice } from '../../../flow/ProblemNotice'
import { useServerStrings } from '../../../flow/serverStrings'
import { useT } from '../../../i18n/I18n'

const DEBOUNCE_MS = 250

/** ARIA 1.2 combobox with a listbox popup: typeahead over GET /formulary/search (limit 20, debounced, no fuzzy matching).
 * Nothing is preselected and no guess is filled in. Each option shows brand names, generic name and strengths so the person can compare with the paper. */
export function FormularyPicker({ onPick, label }: { onPick: (e: FormularyEntry) => void; label?: string }) {
  const { t } = useT()
  const { s } = useServerStrings()
  const uid = useId()
  const listId = `${uid}-list`
  const [q, setQ] = useState('')
  const [results, setResults] = useState<FormularyEntry[] | null>(null)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [problem, setProblem] = useState<Problem | null>(null)
  const [loading, setLoading] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const text = q.trim()
    if (!text) {
      setResults(null)
      setLoading(false)
      return
    }
    const ctl = new AbortController()
    setLoading(true)
    const timer = setTimeout(() => {
      searchFormulary(text, 20, ctl.signal)
        .then((r) => {
          setResults(r.results)
          setProblem(null)
          setActive(-1)
          setOpen(true)
          setLoading(false)
        })
        .catch((e) => {
          if (isAbort(e)) return
          setProblem(toProblem(e))
          setLoading(false)
        })
    }, DEBOUNCE_MS)
    return () => {
      clearTimeout(timer)
      ctl.abort()
    }
  }, [q])

  const pick = (e: FormularyEntry) => {
    setOpen(false)
    onPick(e)
  }
  const n = results?.length ?? 0
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!open && results) setOpen(true)
      else setActive((a) => (n ? (a + 1) % n : -1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => (n ? (a <= 0 ? n - 1 : a - 1) : -1))
    } else if (e.key === 'Enter' && open && active >= 0 && results) {
      e.preventDefault()
      pick(results[active])
    } else if (e.key === 'Escape' && open) {
      e.preventDefault()
      e.stopPropagation()
      setOpen(false)
    } else if (e.key === 'Home' && open && n) {
      e.preventDefault()
      setActive(0)
    } else if (e.key === 'End' && open && n) {
      e.preventDefault()
      setActive(n - 1)
    }
  }

  return (
    <div className="picker">
      <label htmlFor={`${uid}-input`} className="field-label">
        {label ?? s('picker.search', undefined, t('ui.flow.picker.search'))}
      </label>
      <div className="picker-input">
        <Icon name="search" size={20} />
        <input
          ref={input}
          id={`${uid}-input`}
          role="combobox"
          aria-expanded={open && n > 0}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open && active >= 0 ? `${uid}-opt-${active}` : undefined}
          autoComplete="off"
          spellCheck={false}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={onKey}
          onBlur={() => setOpen(false)}
          onFocus={() => results && setOpen(true)}
        />
      </div>
      <ul id={listId} role="listbox" aria-label={t('ui.flow.picker.listbox')} className="picker-list" hidden={!open || n === 0}>
        {results?.map((r, i) => (
          <li
            key={r.id}
            id={`${uid}-opt-${i}`}
            role="option"
            aria-selected={i === active}
            className={i === active ? 'active' : ''}
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => pick(r)}
            onMouseMove={() => setActive(i)}
          >
            <strong>{r.generic}</strong>
            <span className="small">
              {s('picker.brand', undefined, t('ui.flow.picker.brand'))}: {r.brand_names.join(', ')}
            </span>
            <span className="small">
              {s('picker.strength', undefined, t('ui.flow.picker.strength'))}: {r.available_strengths.join(', ')}
            </span>
          </li>
        ))}
      </ul>
      <p className="sr-only" role="status" aria-live="polite">
        {loading ? '' : results ? (n ? t('ui.flow.picker.count', { n }) : s('picker.no_results', undefined, t('ui.flow.picker.none'))) : ''}
      </p>
      {results && !n && !loading ? <p className="small muted">{s('picker.no_results', undefined, t('ui.flow.picker.none'))}</p> : null}
      {problem ? <ProblemNotice problem={problem} /> : null}
    </div>
  )
}
