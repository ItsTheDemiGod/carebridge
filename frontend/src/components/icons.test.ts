import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { ICON_NAMES, Icon } from './icons'

describe('icon set', () => {
  it('has at most 6 icons beyond the 20 drawn in 6a and 6b (menu, still, zoomin, zoomout, chevron, reset)', () => {
    expect(ICON_NAMES.length).toBeLessThanOrEqual(26)
  })
  for (const name of ICON_NAMES)
    it(`${name}: 24 px grid, 1.5 px round stroke in currentColor, no fill, drawn content, decorative by default`, () => {
      const html = renderToStaticMarkup(createElement(Icon, { name }))
      expect(html).toContain('viewBox="0 0 24 24"')
      expect(html).toContain('fill="none"')
      expect(html).toContain('stroke="currentColor"')
      expect(html).toContain('stroke-width="1.5"')
      expect(html).toContain('stroke-linecap="round"')
      expect(html).toContain('stroke-linejoin="round"')
      expect(html).toContain('aria-hidden="true"')
      expect(html).toContain('focusable="false"')
      expect(html).toMatch(/<(path|circle|rect)\b/)
      const inner = html.slice(html.indexOf('>') + 1)
      expect(inner, 'no fill or colour leaks inside').not.toMatch(/fill="(?!none)|stroke="(?!currentColor)/)
      expect(inner).not.toMatch(/\bd=""/)
    })
  it('a labelled icon is exposed as an image with that text', () => {
    const html = renderToStaticMarkup(createElement(Icon, { name: 'check', label: 'Done' }))
    expect(html).toContain('role="img"')
    expect(html).toContain('aria-label="Done"')
    expect(html).not.toContain('aria-hidden')
  })
})
