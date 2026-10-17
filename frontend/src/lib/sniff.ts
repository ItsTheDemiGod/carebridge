/* Browser-side file checks are a convenience only: the backend re-checks type, size and pixels and stays the authority. */
export type Sniffed = 'png' | 'jpeg' | 'pdf' | 'other'

export function sniff(head: Uint8Array): Sniffed {
  const b = (...xs: number[]) => xs.every((x, i) => head[i] === x)
  if (b(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)) return 'png'
  if (b(0xff, 0xd8, 0xff)) return 'jpeg'
  if (b(0x25, 0x50, 0x44, 0x46)) return 'pdf'
  return 'other'
}

export const MIME: Record<'png' | 'jpeg', string> = { png: 'image/png', jpeg: 'image/jpeg' }

export type FileCheck = { ok: true; type: string } | { ok: false; reason: 'pdf' | 'unsupported' | 'too_large' | 'empty' }

export async function checkFile(file: Blob, maxBytes: number): Promise<FileCheck> {
  if (file.size === 0) return { ok: false, reason: 'empty' }
  const kind = sniff(new Uint8Array(await file.slice(0, 8).arrayBuffer()))
  if (kind === 'pdf') return { ok: false, reason: 'pdf' }
  if (kind === 'other') return { ok: false, reason: 'unsupported' }
  if (file.size > maxBytes) return { ok: false, reason: 'too_large' }
  return { ok: true, type: MIME[kind] }
}
