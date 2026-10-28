// GitHub Pages has no single-page-app fallback: an unknown path is answered with 404.html. Copy index.html so deep links and reloads reach the router.
import { copyFileSync } from 'node:fs'
import { join } from 'node:path'

const dir = process.argv[2] ?? 'dist-demo'
copyFileSync(join(dir, 'index.html'), join(dir, '404.html'))
console.log(`wrote ${join(dir, '404.html')}`)
