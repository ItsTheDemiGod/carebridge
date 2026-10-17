import { useT } from '../i18n/I18n'
import { Icon } from './icons'

const NODES = ['n1', 'n2', 'n3', 'n4', 'n5'] as const
const YOURS = new Set(['n1', 'n3'])

/** Simple SVG diagram: photo, reading, your check, explanation, interactions, then found / could not check.
 *  Labels come from strings. Below 48 rem the vertical version below is shown instead (same five steps and the same two outcomes). */
export function PipelineDiagram() {
  const { t } = useT()
  return (
    <svg className="pipeline" viewBox="0 0 1000 330" role="img" aria-label={t('ui.how.fig.alt')}>
      {NODES.map((n, i) => {
        const x = i * 210
        const yours = YOURS.has(n)
        return (
          <g key={n}>
            <rect x={x} y={30} width={160} height={90} rx={14} className={yours ? 'pl-node pl-yours' : 'pl-node'} />
            <text x={x + 16} y={60} className="pl-num">{`0${i + 1}`}</text>
            <text x={x + 16} y={96} className="pl-title">
              {t(`ui.how.${n}.title`)}
            </text>
            {yours ? (
              <text x={x} y={146} className="pl-small">
                {t('ui.how.you')}
              </text>
            ) : null}
            {i < NODES.length - 1 ? <path d={`M${x + 166} 75h38m-8-7l8 7-8 7`} className="pl-arrow" /> : null}
          </g>
        )
      })}
      <path d="M880 120v55M880 175H670v50M880 175h10v50" className="pl-arrow" fill="none" />
      <path d="M664 217l6 8 6-8M884 217l6 8 6-8" className="pl-arrow" fill="none" />
      <rect x={560} y={232} width={220} height={92} rx={14} className="pl-found" />
      <Icon name="alert" size={30} x={655} y={242} className="pl-ic-found" />
      <text x={670} y={304} textAnchor="middle" className="pl-title pl-found-text">
        {t('ui.how.found')}
      </text>
      <rect x={800} y={232} width={190} height={92} rx={14} className="pl-unchecked" />
      <Icon name="help" size={30} x={880} y={242} className="pl-ic-unk" />
      <text x={895} y={304} textAnchor="middle" className="pl-title pl-unchecked-text">
        {t('ui.how.unchecked')}
      </text>
    </svg>
  )
}

/** The same pipeline for phones: five steps top to bottom, then the two outcomes side by side (stacked on very narrow screens). Nothing is hidden. */
export function PipelineVertical() {
  const { t } = useT()
  return (
    <div className="pl-vertical" role="group" aria-label={t('ui.how.fig.alt')}>
      <ol>
        {NODES.map((n, i) => (
          <li key={n} className={YOURS.has(n) ? 'plv-node plv-yours' : 'plv-node'}>
            <span className="plv-num" aria-hidden="true">{`0${i + 1}`}</span>
            <span className="plv-title">{t(`ui.how.${n}.title`)}</span>
            {YOURS.has(n) ? <span className="plv-you"><Icon name="check" size={16} />{t('ui.how.you')}</span> : null}
          </li>
        ))}
      </ol>
      <ul className="plv-outcomes">
        <li className="plv-found">
          <Icon name="alert" size={28} />
          <span>{t('ui.how.found')}</span>
        </li>
        <li className="plv-unchecked">
          <Icon name="help" size={28} />
          <span>{t('ui.how.unchecked')}</span>
        </li>
      </ul>
    </div>
  )
}
