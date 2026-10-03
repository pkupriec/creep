import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, retries: 0,
  timeout: 30000, expect: { timeout: 7000 }, reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5178', viewport: { width: 1720, height: 1120 }, browserName: 'chromium', trace: 'retain-on-failure' },
  webServer: { command: 'npm run dev', url: 'http://127.0.0.1:5178', reuseExistingServer: false, timeout: 30000 },
});
