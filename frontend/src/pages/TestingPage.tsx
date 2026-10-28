import { Notice } from '../components/Badges'
import { Icon } from '../components/icons'
import { Container, SectionHeading } from '../components/Layout'
import raw from '../data/testing.generated.json'
import { fill } from '../flow/serverStrings'
import { useT } from '../i18n/I18n'
import { usePageTitle } from './usePageTitle'

/* The figures come ONLY from src/data/testing.generated.json (scripts/build_testing_page_data.py). This page holds no number and no sentence of its own:
 * every text is a ui.testing.* string; {placeholders} in them are filled from each entry's params. */
type Entry = {
  id: string
  group: string
  label: string
  value: number
  unit: 'ratio' | 'count'
  source: string
  measures: string
  data: string
  params: Record<string, string | number>
  caveat: string | null
  split: 'dev' | 'test'
  date: string
  n?: number
  of?: number
}
type TestEntry = Omit<Entry, 'unit' | 'params' | 'caveat' | 'split'> & {
  unit: 'ratio' | 'count' | 'seconds'
  params: Record<string, string | number>
  split: 'test'
  ci?: [number, number]
  ci_kind?: 'wilson' | 'bootstrap'
  dev?: number
  dev_outside?: boolean
}
type TestData = {
  run: boolean
  date: string
  params: Record<string, string | number>
  groups: string[]
  entries: TestEntry[]
  also: { doc: string; source: string; per_doc: string }
}
type Cell = { k: number | null; n: number | null; value: number | null; wilson: [number, number] | null; bootstrap: [number, number] | null }
type StressEntry = { id: string; group: string; label: string; measures: string; params: Record<string, string | number>; cells: Record<string, Cell>; source: string; split: 'stress'; date: string; no_kn?: boolean; passed?: boolean; limit?: 'zero' | 'all' }
type StressData = { run: boolean; date: string; conditions: string[]; params: Record<string, string | number>; groups: string[]; entries: StressEntry[]; also: { doc: string; source: string; per_doc: string } }
type Data = { final_test: { run: boolean }; test: TestData; stress_ext: StressData; limits_params: Record<string, number>; groups: string[]; entries: Entry[] }
const DATA = raw as unknown as Data
const LIMITS = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6', 'l7', 'l8', 'l9', 'l10'] as const
/** test group -> the string id of its data line */
const TEST_DATA: Record<string, string> = { ex_raw: 'ex', ex_norm: 'ex', flags: 'flags', safety: 'safety', expl: 'expl', ops: 'ops' }

/** ratios as percentages with one decimal, counts as integers: Western digits in every language (toFixed does not localise) */
export const show = (e: Pick<Entry, 'value' | 'unit'>) => (e.unit === 'ratio' ? `${(e.value * 100).toFixed(1)}%` : String(e.value))

const pct = (x: number) => `${(x * 100).toFixed(1)}%`
const signed = (x: number, d: number) => `${x > 0 ? '+' : ''}${x.toFixed(d)}`

export function TestingPage() {
  const { t } = useT()
  usePageTitle('ui.title.testing')
  const lp = DATA.limits_params
  const cols = ['measure', 'result', 'data', 'measures', 'source'] as const
  return (
    <Container as="section" className="page-wide testing-page">
      <SectionHeading as="h1" label={t('ui.testing.label')} title={t('ui.testing.title')} />
      <p className="lede">{t('ui.testing.page.lede')}</p>

      <section aria-labelledby="tm-h" className="method">
        <h2 id="tm-h" className="h3-like">{t('ui.testing.method.title')}</h2>
        <div className="method-list">
          {(['dev', 'test', 'synthetic'] as const).map((k) => (
            <p key={k}>{t(`ui.testing.method.${k}`)}</p>
          ))}
        </div>
      </section>

      {DATA.final_test.run ? <TestSection /> : (
        <section aria-labelledby="tf-h" className="tgroup">
          <h2 id="tf-h" className="h3-like">{t('ui.testing.final.title')}</h2>
          <p className="t-notrun">{t('ui.testing.final.not_run')}</p>
        </section>
      )}

      {DATA.stress_ext.run ? <StressSection /> : null}

      <section aria-labelledby="td-h" className="tdev">
        <h2 id="td-h" className="h3-like">{t('ui.testing.t.dev_heading')}</h2>
        <p className="muted">{t('ui.testing.t.dev_note')}</p>
      </section>

      {DATA.groups.map((g) => {
        const rows = DATA.entries.filter((e) => e.group === g)
        const dataText = (e: Entry) => fill(t(e.data), { ...e.params, ...lp })
        const scope = (e: Entry) => `${t(`ui.testing.split.${e.split}`)} · ${fill(t('ui.testing.date'), { date: e.date })}`
        // one shared data line per group when every row measures on the same data; otherwise each row says its own
        const shared = rows.every((r) => dataText(r) === dataText(rows[0]) && scope(r) === scope(rows[0]))
        const gcols = shared ? cols.filter((c) => c !== 'data') : cols
        return (
          <section key={g} aria-labelledby={`tg-${g}`} className="tgroup">
            <h2 id={`tg-${g}`} className="h3-like">{t(`ui.testing.g.${g}`)}</h2>
            {shared ? (
              <p className="group-data">
                <strong>{dataText(rows[0])}</strong>
                <span className="muted small">{scope(rows[0])}</span>
              </p>
            ) : null}
            <div className="table-wrap" tabIndex={0} role="region" aria-labelledby={`tg-${g}`}>
              <table className="testing-table">
                <caption className="sr-only">{`${t('ui.testing.table.caption')} ${t(`ui.testing.g.${g}`)}`}</caption>
                <thead>
                  <tr>
                    {gcols.map((c) => (
                      <th key={c} scope="col">{t(`ui.testing.col.${c}`)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((e) => {
                    const params = { ...e.params, ...lp }
                    return (
                      <tr key={e.id} data-figure={e.id}>
                        <th scope="row" data-label={t('ui.testing.col.measure')}>{t(e.label)}</th>
                        <td data-label={t('ui.testing.col.result')} className="t-result">
                          <strong>{show(e)}</strong>
                          {e.of !== undefined && e.n !== undefined ? <span className="muted small">{fill(t('ui.testing.k_of_n'), { n: e.n, of: e.of })}</span> : null}
                        </td>
                        {shared ? null : (
                          <td data-label={t('ui.testing.col.data')}>
                            <p>{dataText(e)}</p>
                            <p className="muted small">{scope(e)}</p>
                          </td>
                        )}
                        <td data-label={t('ui.testing.col.measures')} className="t-measures">
                          <p>{t(e.measures)}</p>
                          {e.caveat ? (
                            <p className="t-caveat">
                              <strong>{t('ui.testing.caveat_label')}</strong> {fill(t(e.caveat), { ...params, ...(e.n !== undefined ? { n: e.n } : {}) })}
                            </p>
                          ) : null}
                        </td>
                        <td data-label={t('ui.testing.col.source')}>
                          <code className="t-source">{e.source}</code>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )
      })}


      <section aria-labelledby="tl-h" className="tlimits">
        <Notice tone="important">
          <h2 id="tl-h" className="h3-like">{t('ui.testing.limits.title')}</h2>
          <ol className="limits-list">
            {LIMITS.map((k) => (
              <li key={k}>{fill(t(`ui.testing.limits.${k}`), lp)}</li>
            ))}
          </ol>
        </Notice>
      </section>
    </Container>
  )
}

function TestSection() {
  const { t } = useT()
  const T = DATA.test
  const gp = T.params
  const resolve = (p: Record<string, string | number>) => Object.fromEntries(Object.entries(p).map(([k, v]) => [k, typeof v === 'string' && v.startsWith('ui.') ? t(v) : v]))
  const value = (e: TestEntry) => (e.unit === 'ratio' ? pct(e.value) : e.unit === 'seconds' ? fill(t('ui.testing.t.seconds'), { v: e.value.toFixed(1) }) : String(e.value))
  const devText = (e: TestEntry) => (e.unit === 'ratio' ? pct(e.dev as number) : String(e.dev))
  const diff = (e: TestEntry) => {
    const d = e.value - (e.dev as number)
    return e.unit === 'ratio' ? fill(t('ui.testing.t.pts'), { v: signed(d * 100, 1) }) : signed(d, 0)
  }
  return (
    <section aria-labelledby="tf-h" className="tgroup tfinal">
      <h2 id="tf-h" className="h3-like">{t('ui.testing.final.title')}</h2>
      <p className="lede">{fill(t('ui.testing.t.intro'), gp)}</p>
      <p className="t-run">{fill(t('ui.testing.t.run'), gp)}</p>
      {T.groups.map((g) => {
        const rows = T.entries.filter((e) => e.group === g)
        return (
          <section key={g} aria-labelledby={`tt-${g}`} className="tgroup">
            <h3 id={`tt-${g}`} className="h3-like">{t(`ui.testing.t.g.${g}`)}</h3>
            <p className="group-data">
              <strong>{fill(t(`ui.testing.t.d.${TEST_DATA[g]}`), gp)}</strong>
              <span className="muted small">{`${t('ui.testing.split.test')} · ${fill(t('ui.testing.t.rundate'), { date: T.date })}`}</span>
            </p>
            <div className="table-wrap" tabIndex={0} role="region" aria-labelledby={`tt-${g}`}>
              <table className="testing-table">
                <caption className="sr-only">{`${t('ui.testing.table.caption')} ${t(`ui.testing.t.g.${g}`)}`}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t('ui.testing.col.measure')}</th>
                    <th scope="col">{t('ui.testing.t.col_test')}</th>
                    <th scope="col">{t('ui.testing.t.col_dev')}</th>
                    <th scope="col">{t('ui.testing.col.measures')}</th>
                    <th scope="col">{t('ui.testing.col.source')}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((e) => {
                    const params = { ...gp, ...resolve(e.params) }
                    return (
                      <tr key={e.id} data-figure={e.id}>
                        <th scope="row" data-label={t('ui.testing.col.measure')}>{fill(t(e.label), params)}</th>
                        <td data-label={t('ui.testing.t.col_test')} className="t-result">
                          <strong>{value(e)}</strong>
                          {e.of !== undefined && e.n !== undefined ? <span className="muted small">{fill(t('ui.testing.k_of_n'), { n: e.n, of: e.of })}</span> : null}
                          {e.ci ? (
                            <span className="muted small t-ci">{`[${pct(e.ci[0])}, ${pct(e.ci[1])}] ${fill(t(e.ci_kind === 'bootstrap' ? 'ui.testing.t.ci_boot' : 'ui.testing.t.ci_wilson'), gp)}`}</span>
                          ) : null}
                        </td>
                        <td data-label={t('ui.testing.t.col_dev')} className="t-dev">
                          {e.dev !== undefined ? (
                            <>
                              <strong>{devText(e)}</strong>
                              <span className="muted small">{fill(t('ui.testing.t.diff'), { v: diff(e) })}</span>
                              {e.dev_outside ? <span className="t-outside small"><Icon name="alert" />{t('ui.testing.t.outside')}</span> : null}
                            </>
                          ) : (
                            <span className="muted small">{t('ui.testing.t.no_dev')}</span>
                          )}
                        </td>
                        <td data-label={t('ui.testing.col.measures')} className="t-measures">
                          <p>{fill(t(e.measures), gp)}</p>
                        </td>
                        <td data-label={t('ui.testing.col.source')}>
                          <code className="t-source">{e.source}</code>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )
      })}
      <p className="t-also">{fill(t('ui.testing.t.also'), { ...gp, ...T.also })}</p>
    </section>
  )
}

function StressSection() {
  const { t } = useT()
  const S = DATA.stress_ext
  const gp = S.params
  const resolve = (p: Record<string, string | number>) => Object.fromEntries(Object.entries(p).map(([k, v]) => [k, typeof v === 'string' && v.startsWith('ui.') ? t(v) : v]))
  return (
    <section aria-labelledby="ts-h" className="tgroup tstress">
      <h2 id="ts-h" className="h3-like">{t('ui.testing.s.title')}</h2>
      <p className="lede">{fill(t('ui.testing.s.intro'), gp)}</p>
      <p className="t-run">{fill(t('ui.testing.s.run'), { ...gp, date: S.date })}</p>
      <Notice tone="important"><p>{fill(t('ui.testing.s.deviation'), gp)}</p></Notice>
      {S.groups.map((g) => {
        const rows = S.entries.filter((e) => e.group === g)
        return (
          <section key={g} aria-labelledby={`ts-${g}`} className="tgroup">
            <h3 id={`ts-${g}`} className="h3-like">{t(`ui.testing.s.g.${g}`)}</h3>
            <p className="group-data">
              <strong>{fill(t('ui.testing.s.d.all'), gp)}</strong>
              <span className="muted small">{`${t('ui.testing.split.stress')} · ${fill(t('ui.testing.t.rundate'), { date: S.date })}`}</span>
            </p>
            <div className="table-wrap" tabIndex={0} role="region" aria-labelledby={`ts-${g}`}>
              <table className="testing-table">
                <caption className="sr-only">{`${t('ui.testing.table.caption')} ${t(`ui.testing.s.g.${g}`)}`}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t('ui.testing.col.measure')}</th>
                    {S.conditions.map((c) => (
                      <th key={c} scope="col">{t(`ui.testing.s.col_${c}`)}</th>
                    ))}
                    <th scope="col">{t('ui.testing.col.measures')}</th>
                    <th scope="col">{t('ui.testing.col.source')}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((e) => {
                    const params = { ...gp, ...resolve(e.params) }
                    return (
                      <tr key={e.id} data-sfigure={e.id}>
                        <th scope="row" data-label={t('ui.testing.col.measure')}>
                          {fill(t(e.label), params)}
                          {e.limit ? <span className="muted small t-limit">{t(`ui.testing.s.limit_${e.limit === 'zero' ? 'zero' : 'all'}`)}</span> : null}
                          {e.passed !== undefined ? (
                            <span className={e.passed ? 't-met small' : 't-outside small'}>
                              <Icon name={e.passed ? 'check' : 'alert'} />{t(e.passed ? 'ui.testing.s.met' : 'ui.testing.s.notmet')}
                            </span>
                          ) : null}
                        </th>
                        {S.conditions.map((c) => {
                          const x = e.cells[c]
                          return (
                            <td key={c} data-label={t(`ui.testing.s.col_${c}`)} className="t-result" data-cond={c}>
                              <strong>{x.value === null ? '' : pct(x.value)}</strong>
                              {!e.no_kn && x.k !== null && x.n !== null ? <span className="muted small">{fill(t('ui.testing.k_of_n'), { n: x.k, of: x.n })}</span> : null}
                              {x.wilson ? <span className="muted small t-ci t-wilson">{`[${pct(x.wilson[0])}, ${pct(x.wilson[1])}] ${fill(t('ui.testing.t.ci_wilson'), gp)}`}</span> : null}
                              {x.bootstrap ? <span className="muted small t-ci t-boot">{`[${pct(x.bootstrap[0])}, ${pct(x.bootstrap[1])}] ${fill(t('ui.testing.t.ci_boot'), gp)}`}</span> : null}
                            </td>
                          )
                        })}
                        <td data-label={t('ui.testing.col.measures')} className="t-measures">
                          <p>{fill(t(e.measures), params)}</p>
                        </td>
                        <td data-label={t('ui.testing.col.source')}>
                          <code className="t-source">{e.source}</code>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )
      })}
      <p className="t-also">{fill(t('ui.testing.s.also'), S.also)}</p>
    </section>
  )
}
