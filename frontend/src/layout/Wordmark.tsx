const BRAND = 'CareBridge'

/** Original wordmark: a three-ring bridge arch over a deck line, with a small plus above the keystone. */
export function Wordmark({ className = '' }: { className?: string }) {
  return (
    <span className={`wordmark ${className}`.trim()}>
      <svg viewBox="0 0 40 30" width="40" height="30" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
        <path d="M1.5 25.5h37" />
        <path d="M5 25.5C5 11 35 11 35 25.5" />
        <path d="M11 25.5c0-8 18-8 18 0" />
        <path d="M17 25.5c0-4 6-4 6 0" />
        <path d="M20 3v6M17 6h6" stroke="var(--terracotta)" strokeWidth="1.8" />
      </svg>
      <span className="wordmark-text">{BRAND}</span>
    </span>
  )
}
