import { defineConfig } from '@playwright/test'

// Hosted-sample (GitHub Pages) build, served under /carebridge/ by a Pages-like static server. NO backend runs: any /api request is a failure.
export default defineConfig({
  testDir: 'e2e-demo',
  timeout: 60_000,
  fullyParallel: true,
  workers: 6,
  reporter: [['list']],
  use: { baseURL: 'http://localhost:4174/carebridge/', browserName: 'chromium' },
  webServer: { command: 'npm run build:demo && node scripts/serve-pages.mjs dist-demo 4174 /carebridge/', url: 'http://localhost:4174/carebridge/', reuseExistingServer: true, timeout: 240_000 },
})
