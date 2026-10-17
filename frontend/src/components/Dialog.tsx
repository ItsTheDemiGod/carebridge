import { useEffect, useRef, type ReactNode } from 'react'

/** Modal on the native <dialog> element: focus is trapped and returned by the browser, Escape closes (we route it through onClose). */
export function Dialog({ open, onClose, labelledBy, children, className = '' }: { open: boolean; onClose: () => void; labelledBy: string; children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal()
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog
      ref={ref}
      className={`dialog ${className}`.trim()}
      aria-labelledby={labelledBy}
      onCancel={(e) => {
        e.preventDefault()
        onClose()
      }}
    >
      {open ? children : null}
    </dialog>
  )
}
