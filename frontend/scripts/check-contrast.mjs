// WCAG 2.2 contrast check for every text-on-background and UI-component pair the design uses.
// Colours are read from src/styles/tokens.css. Exit code 1 if any pair fails.   npm run check:contrast
import { readFileSync } from 'node:fs'

const css = readFileSync(new URL('../src/styles/tokens.css', import.meta.url), 'utf8')
const tok = Object.fromEntries([...css.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)].map((m) => [m[1], m[2]]))

const lin = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => lin(parseInt(hex.slice(i, i + 2), 16) / 255))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
const ratio = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

const TEXT = 4.5 // normal text
const UI = 3 // large text, icons, control boundaries, focus rings
const sev = ['major', 'moderate', 'minor', 'unknown']
const pairs = [
  ['ink', 'paper', TEXT, 'body text'],
  ['ink', 'paper-2', TEXT, 'body text on second paper'],
  ['ink', 'mist', TEXT, 'text on mist tiles'],
  ['ink', 'sage', TEXT, 'text on sage tiles'],
  ['ink-soft', 'paper', TEXT, 'secondary text'],
  ['ink-soft', 'paper-2', TEXT, 'secondary text on second paper'],
  ['ink-soft', 'mist', TEXT, 'secondary text on mist'],
  ['pine', 'paper', TEXT, 'links, headings'],
  ['pine', 'paper-2', TEXT, 'links on second paper'],
  ['terracotta-ink', 'paper', TEXT, 'accent text'],
  ['terracotta-ink', 'paper-2', TEXT, 'accent text on second paper'],
  ['on-dark', 'pine', TEXT, 'primary button, dark band'],
  ['on-dark', 'pine-deep', TEXT, 'primary button hover, dark band'],
  ['on-dark', 'ink', TEXT, 'footer'],
  ['on-dark-soft', 'pine-deep', TEXT, 'secondary text on dark'],
  ['on-dark-soft', 'ink', TEXT, 'secondary text on footer'],
  ...sev.flatMap((s) => [
    [`sev-${s}`, `sev-${s}-bg`, TEXT, `severity badge ${s}`],
    [`sev-${s}`, 'paper', TEXT, `severity text on paper ${s}`],
  ]),
  ['terracotta', 'paper', UI, 'accent icon, large display accent'],
  ['terracotta', 'paper-2', UI, 'accent icon on second paper'],
  ['pine', 'mist', UI, 'icon on mist'],
  ['line-strong', 'paper', UI, 'control boundary'],
  ['line-strong', 'paper-2', UI, 'control boundary on second paper'],
  ['focus', 'paper', UI, 'focus ring'],
  ['focus', 'paper-2', UI, 'focus ring on second paper'],
  ['focus', 'mist', UI, 'focus ring on mist'],
  ['focus-on-dark', 'pine', UI, 'focus ring on dark'],
  ['focus-on-dark', 'pine-deep', UI, 'focus ring on dark band'],
  ['focus-on-dark', 'ink', UI, 'focus ring on footer'],
]

let failed = 0
console.log('foreground / background'.padEnd(40), 'ratio'.padStart(6), 'need'.padStart(5), '  result  use')
for (const [fg, bg, min, use] of pairs) {
  if (!tok[fg] || !tok[bg]) {
    console.log(`MISSING token: ${fg} or ${bg}`)
    failed++
    continue
  }
  const r = ratio(tok[fg], tok[bg])
  const ok = r >= min
  if (!ok) failed++
  console.log(`${fg} / ${bg}`.padEnd(40), r.toFixed(2).padStart(6), String(min).padStart(5), ok ? '  pass  ' : '  FAIL  ', use)
}
console.log(`\n${pairs.length - failed} of ${pairs.length} pairs pass`)
process.exit(failed ? 1 : 0)
