/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

/* Two builds. Normal: base "/", the whole app. `--mode pages` (npm run build:demo): the hosted sample only, base "/carebridge/" (override with PAGES_BASE):
 * the real-flow routes are replaced by a stub module, so their pages are not bundled, and the API client answers everything from the bundled fixtures. */
export default defineConfig(({ mode }) => {
  const pages = mode === 'pages'
  return {
    base: pages ? (process.env.PAGES_BASE ?? '/carebridge/') : '/',
    plugins: [react(), tailwindcss()],
    define: { 'import.meta.env.VITE_DEMO_ONLY': JSON.stringify(pages ? '1' : '0') },
    resolve: pages ? { alias: [{ find: /^\.\/routes\.real$/, replacement: fileURLToPath(new URL('./src/routes.real.stub.tsx', import.meta.url)) }] } : {},
    server: { proxy: { '/api': 'http://localhost:8000' } },
    preview: pages ? {} : { proxy: { '/api': 'http://localhost:8000' } },
    test: { environment: 'node', include: ['src/**/*.test.ts'] },
  }
})
