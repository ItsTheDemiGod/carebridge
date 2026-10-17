import { defineConfig } from '@playwright/test'

/* Live end-to-end against the REAL backend (port 8000, started with ALLOWED_ORIGINS that includes http://localhost:4173) and a local Ollama model.
 * Dev images from data/rendered/ only. Run: npm run build; npx vite preview --port 4173 --strictPort; npx playwright test -c playwright.live.config.ts */
export default defineConfig({
  testDir: 'e2e/live',
  timeout: 20 * 60_000,
  workers: 1,
  fullyParallel: false,
  reporter: [['list']],
  use: { baseURL: 'http://localhost:4173', browserName: 'chromium', viewport: { width: 1280, height: 900 } },
})
