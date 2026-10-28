import { describe, expect, it } from 'vitest'
import { stripBase, withBase } from './mode'

describe('base path helpers', () => {
  it('strips the Pages base from a browser pathname and leaves other paths alone', () => {
    expect(stripBase('/carebridge/demo/review', '/carebridge/')).toBe('/demo/review')
    expect(stripBase('/carebridge/', '/carebridge/')).toBe('/')
    expect(stripBase('/carebridge', '/carebridge/')).toBe('/')
    expect(stripBase('/carebridgeX/demo', '/carebridge/')).toBe('/carebridgeX/demo')
    expect(stripBase('/demo', '/')).toBe('/demo')
  })
  it('puts public files under the base', () => {
    expect(withBase('demo/sample-document.png', '/carebridge/')).toBe('/carebridge/demo/sample-document.png')
    expect(withBase('/photos/a.jpg', '/carebridge/')).toBe('/carebridge/photos/a.jpg')
    expect(withBase('photos/a.jpg', '/')).toBe('/photos/a.jpg')
  })
})
