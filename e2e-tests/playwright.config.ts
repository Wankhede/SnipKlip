import { defineConfig, devices } from '@playwright/test';

const BACKEND = process.env.SNIPKLIP_BACKEND_URL || 'http://127.0.0.1:8082';
const FRONTEND = process.env.SNIPKLIP_FRONTEND_URL || 'http://127.0.0.1:8083';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['json', { outputFile: 'reports/results.json' }]
  ],
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    baseURL: FRONTEND,
    extraHTTPHeaders: { Accept: 'application/json' }
  },
  projects: [
    {
      name: 'api',
      testMatch: /api\/.*\.spec\.ts/,
      use: { baseURL: BACKEND }
    },
    {
      name: 'chromium',
      testMatch: /ui\/.*\.spec\.ts/,
      use: { ...devices['Desktop Chrome'], baseURL: FRONTEND }
    }
  ]
});
