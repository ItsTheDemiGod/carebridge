import { Notice } from '../components/Badges'
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
type Data = { final_test: { run: boolean }; limits_params: Record<string, number>; groups: string[]; entries: Entry[] }
const DATA = raw as unknown as Data
const LIMITS = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6', 'l7'] as const

/** ratios as percentages with one decimal, counts as integers: Western digits in every language (toFixed does not localise) */
export const show = (e: Pick<Entry, 'value' | 'unit'>) => (e.unit === 'ratio' ? `${(e.value * 100).toFixed(1)}%` : String(e.value))

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

      {DATA.groups.map((g) => {
        const rows = DATA.entries.filter((e) => e.group === g)
        return (
          <section key={g} aria-labelledby={`tg-${g}`} className="tgroup">
            <h2 id={`tg-${g}`} className="h3-like">{t(`ui.testing.g.${g}`)}</h2>
            <div className="table-wrap" tabIndex={0} role="region" aria-labelledby={`tg-${g}`}>
              <table className="testing-table">
                <caption className="sr-only">{`${t('ui.testing.table.caption')} ${t(`ui.testing.g.${g}`)}`}</caption>
                <thead>
                  <tr>
                    {cols.map((c) => (
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
                        <td data-label={t('ui.testing.col.data')}>
                          <p>{fill(t(e.data), params)}</p>
                          <p className="muted small">
                            {t(`ui.testing.split.${e.split}`)} · {fill(t('ui.testing.date'), { date: e.date })}
                          </p>
                        </td>
                        <td data-label={t('ui.testing.col.measures')}>
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

      {!DATA.final_test.run ? (
        <section aria-labelledby="tf-h" className="tgroup">
          <h2 id="tf-h" className="h3-like">{t('ui.testing.final.title')}</h2>
          <p className="t-notrun">{t('ui.testing.final.not_run')}</p>
        </section>
      ) : null}

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
