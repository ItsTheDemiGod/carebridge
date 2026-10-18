import { defineConfig } from '@playwright/test'

/* Live end-to-end against the REAL backend (port 8000, started with ALLOWED_ORIGINS that includes http://localhost:4173) and a local Ollama model.
 * Dev images from data/rendered/ only. Run: npm run build; npx vite preview --port 4173 --strictPort; npx playwright test -c playwright.live.config.ts */
export default defineConfig({
  testDir: 'e2e/live',
  timeout: 20 * 60_000, // whole flow: dominated by the local model; ordinary UI steps are bounded below
  expect: { timeout: 45_000 }, // ordinary expectations: a missing control must fail within about a minute

  workers: 1,
  fullyParallel: false,
  reporter: [['list']],
  use: { actionTimeout: 45_000, navigationTimeout: 60_000, baseURL: 'http://localhost:4173', browserName: 'chromium', viewport: { width: 1280, height: 900 } },
})
