import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: 'e2e',
  testIgnore: '**/live/**', // live runs need the real model: playwright.live.config.ts
  timeout: 60_000,
  fullyParallel: true,
  reporter: [['list']],
  use: { baseURL: 'http://localhost:4173', browserName: 'chromium' },
  // the backend (port 8000) is needed only by the privacy-page test that expects the live notice; start it separately
  webServer: { command: 'npm run build && npx vite preview --port 4173 --strictPort', url: 'http://localhost:4173', reuseExistingServer: true, timeout: 240_000 },
})
