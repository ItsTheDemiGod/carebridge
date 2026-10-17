import { describe, expect, it } from 'vitest'
import { checkFile, sniff } from './sniff'

const blob = (bytes: number[], pad = 0) => new Blob([new Uint8Array([...bytes, ...new Array(pad).fill(0)])])
const PNG = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]

describe('file sniffing', () => {
  it('recognises PNG, JPEG and PDF by magic bytes, not by name', () => {
    expect(sniff(new Uint8Array(PNG))).toBe('png')
    expect(sniff(new Uint8Array([0xff, 0xd8, 0xff, 0xe0]))).toBe('jpeg')
    expect(sniff(new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d]))).toBe('pdf')
    expect(sniff(new Uint8Array([1, 2, 3, 4]))).toBe('other')
  })
  it('rejects pdf, unknown, empty and oversize files; accepts a small png', async () => {
    expect(await checkFile(blob([0x25, 0x50, 0x44, 0x46]), 100)).toEqual({ ok: false, reason: 'pdf' })
    expect(await checkFile(blob([1, 2, 3]), 100)).toEqual({ ok: false, reason: 'unsupported' })
    expect(await checkFile(blob([]), 100)).toEqual({ ok: false, reason: 'empty' })
    expect(await checkFile(blob(PNG, 200), 100)).toEqual({ ok: false, reason: 'too_large' })
    expect(await checkFile(blob(PNG, 10), 100)).toEqual({ ok: true, type: 'image/png' })
  })
})
