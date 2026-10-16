import type { ElementType, HTMLAttributes, ReactNode } from 'react'

export function Container({ children, as: Tag = 'div', className = '', ...rest }: { children: ReactNode; as?: ElementType; className?: string } & HTMLAttributes<HTMLElement>) {
  return (
    <Tag className={`container ${className}`.trim()} {...rest}>
      {children}
    </Tag>
  )
}

export function Rule({ className = '' }: { className?: string }) {
  return <hr className={`rule ${className}`.trim()} />
}

/** Numbered small-caps label above a serif heading. `number` is a digit string such as "01". */
export function SectionHeading({ number, label, title, id, as: H = 'h2', className = '' }: { number?: string; label: string; title: ReactNode; id?: string; as?: 'h1' | 'h2' | 'h3'; className?: string }) {
  return (
    <header className={`section-heading ${className}`.trim()}>
      <p className="label">
        {number ? <span className="label-num">{number}</span> : null}
        <span>{label}</span>
      </p>
      <H id={id} className={H === 'h1' ? 'h1' : 'h2'}>
        {title}
      </H>
    </header>
  )
}
