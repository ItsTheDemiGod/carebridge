// Post-build step of the hosted-sample build. GitHub Pages has no single-page-app fallback: an unknown path is answered with 404.html,
// so copy index.html to 404.html (deep links and reloads then reach the router). Also drop photos/raw: the full-size originals live only on the
// author's computer (gitignored) and must never be deployed, even when a local build copies them from public/.
import { copyFileSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const dir = process.argv[2] ?? 'dist-demo'
rmSync(join(dir, 'photos', 'raw'), { recursive: true, force: true })
copyFileSync(join(dir, 'index.html'), join(dir, '404.html'))
console.log(`wrote ${join(dir, '404.html')}; removed ${join(dir, 'photos', 'raw')}`)
