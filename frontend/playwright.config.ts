import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests', fullyParallel: false, workers: 1, timeout: 60000,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5179', trace: 'retain-on-failure',
    ...devices['Desktop Edge'], channel: 'msedge', headless: true },
  // Opt-in for externally managed local test servers (e.g. Windows teardown).
  // Those servers must disable dotenv and clear LLM credentials; never use production.
  webServer: process.env.E2E_EXTERNAL_SERVERS === 'true' ? undefined : [
    { command: '..\\.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app --app-dir .. --port 8011 --no-access-log',
      url: 'http://127.0.0.1:8011/api/health', timeout: 60000, reuseExistingServer: false,
      env: { PYTHON_DOTENV_DISABLED: '1', LLM_API_KEY: '', LLM_MODEL: '', LLM_BASE_URL: 'http://127.0.0.1:9/v1' } },
    { command: 'npm run dev -- --port 5179 --strictPort', url: 'http://127.0.0.1:5179',
      timeout: 60000, reuseExistingServer: false, env: { API_PROXY_TARGET: 'http://127.0.0.1:8011' } },
  ],
})
