import { Icon } from './icons'
import { useT } from '../i18n/I18n'

/** The "why you confirm first" illustration: a garbled reading next to the formulary pick. Obviously made-up text;
 *  the caption below says so. All text comes from strings; foreignObject lets Tamil and Hindi lines wrap inside the boxes. */
export function ConfirmFigure() {
  const { t } = useT()
  return (
    <figure className="confirm-figure">
      <svg viewBox="0 0 440 330" role="img" aria-label={`${t('ui.confirm.fig.read')} → ${t('ui.confirm.fig.pick')}`}>
        <rect x="8" y="8" width="424" height="96" rx="14" className="cf-bad" />
        <foreignObject x="26" y="14" width="388" height="62">
          <div className="cf-text">{t('ui.confirm.fig.read')}</div>
        </foreignObject>
        <path d="M28 84c30-6 60 6 90 0s60-6 90 0 60 6 90 0 50-4 70 0" className="cf-wavy" />
        <path d="M120 116v56m-9-10l9 10 9-10" className="cf-arrow" />
        <g transform="translate(150 122)">
          <rect width="270" height="44" rx="22" className="cf-tag" />
          <foreignObject x="14" y="2" width="242" height="40">
            <div className="cf-tag-text">{t('ui.confirm.fig.you')}</div>
          </foreignObject>
        </g>
        <rect x="8" y="190" width="424" height="112" rx="14" className="cf-good" />
        <foreignObject x="26" y="200" width="330" height="92">
          <div className="cf-text cf-text-good">{t('ui.confirm.fig.pick')}</div>
        </foreignObject>
        <g transform="translate(372 222)" className="cf-check">
          <circle cx="24" cy="24" r="24" />
          <path d="M13 25l8 8 15-17" />
        </g>
      </svg>
      <figcaption className="small muted">
        <Icon name="info" size={16} /> {t('ui.confirm.fig.caption')}
      </figcaption>
    </figure>
  )
}
