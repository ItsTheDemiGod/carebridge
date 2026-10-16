import type { ReactNode } from 'react'
import { Icon, type IconName } from './icons'

export function Tag({ children, tone = 'neutral', icon }: { children: ReactNode; tone?: 'neutral' | 'accent' | 'draft'; icon?: IconName }) {
  return (
    <span className={`tag tag-${tone}`}>
      {icon ? <Icon name={icon} size={16} /> : null}
      <span>{children}</span>
    </span>
  )
}

/* Severity and status are always icon + text + colour, with a different icon shape per level. */
export type Severity = 'major' | 'moderate' | 'minor' | 'unknown'
const SEV_ICON: Record<Severity, IconName> = { major: 'alert', moderate: 'circle-alert', minor: 'info', unknown: 'help' }

export function StatusBadge({ level, children }: { level: Severity; children: ReactNode }) {
  return (
    <span className={`status status-${level}`}>
      <Icon name={SEV_ICON[level]} size={16} />
      <span>{children}</span>
    </span>
  )
}

const NOTICE_ICON = { info: 'info', caution: 'circle-alert', important: 'alert' } as const

export function Notice({ tone = 'info', title, children }: { tone?: keyof typeof NOTICE_ICON; title?: ReactNode; children: ReactNode }) {
  return (
    <aside className={`notice notice-${tone}`}>
      <Icon name={NOTICE_ICON[tone]} size={26} />
      <div>
        {title ? <p className="notice-title">{title}</p> : null}
        <div className="notice-body">{children}</div>
      </div>
    </aside>
  )
}
