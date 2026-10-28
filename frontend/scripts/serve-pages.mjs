// Serves a built folder the way GitHub Pages does (used by the demo-only tests): files under the base path as they are,
// anything else under the base path answered with 404.html and status 404, anything outside the base path 404. Standard library only.
import { createServer } from 'node:http'
import { existsSync, readFileSync, statSync } from 'node:fs'
import { extname, join, normalize } from 'node:path'

const [dir = 'dist-demo', port = '4174', base = '/carebridge/'] = process.argv.slice(2)
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.woff': 'font/woff', '.webmanifest': 'application/manifest+json', '.ico': 'image/x-icon' }

createServer((req, res) => {
  const url = new URL(req.url ?? '/', 'http://x')
  const send = (status, body, type = 'text/html; charset=utf-8') => {
    res.writeHead(status, { 'Content-Type': type })
    res.end(body)
  }
  if (!url.pathname.startsWith(base)) return send(404, 'not found', 'text/plain')
  let rel = normalize(decodeURIComponent(url.pathname.slice(base.length))).replace(/^([/\\]|\.\.)+/, '')
  let file = join(dir, rel)
  if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html')
  if (existsSync(file) && statSync(file).isFile()) return send(200, readFileSync(file), TYPES[extname(file)] ?? 'application/octet-stream')
  return send(404, readFileSync(join(dir, '404.html')))
}).listen(Number(port), () => console.log(`serving ${dir} at http://localhost:${port}${base}`))
