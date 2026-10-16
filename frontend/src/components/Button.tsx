import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Icon, type IconName } from './icons'

type Variant = 'primary' | 'secondary' | 'quiet'
type Common = { variant?: Variant; icon?: IconName; children: ReactNode; className?: string }

const cls = (v: Variant, extra?: string) => `btn btn-${v}${extra ? ` ${extra}` : ''}`

/** All visible text arrives through children (from the strings file); the component has none of its own. */
export function Button({ variant = 'primary', icon, loading, children, className, disabled, ...rest }: Common & { loading?: boolean } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={cls(variant, className)} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {loading ? <span className="btn-spinner" aria-hidden="true" /> : null}
      <span>{children}</span>
      {icon ? <Icon name={icon} size={20} /> : null}
    </button>
  )
}

export function ButtonLink({ variant = 'primary', icon, to, children, className }: Common & { to: string }) {
  return (
    <Link className={cls(variant, className)} to={to}>
      <span>{children}</span>
      {icon ? <Icon name={icon} size={20} /> : null}
    </Link>
  )
}

/** Inline text link: router link for paths, plain anchor for hash or external targets. */
export function TextLink({ to, children, className }: { to: string; children: ReactNode; className?: string }) {
  const c = `text-link${className ? ` ${className}` : ''}`
  return to.startsWith('#') || /^https?:/.test(to) ? (
    <a className={c} href={to}>
      {children}
    </a>
  ) : (
    <Link className={c} to={to}>
      {children}
    </Link>
  )
}
