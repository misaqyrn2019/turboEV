import { defineConfig } from '@playwright/test'
import path from 'node:path'
import fs from 'node:fs'

const python = fs.existsSync(path.resolve('.venv/Scripts/python.exe')) ? path.resolve('.venv/Scripts/python.exe') : path.resolve('../.venv/Scripts/python.exe')
const qaDir=path.resolve('qa')
fs.mkdirSync(qaDir,{recursive:true})
const dbPath=path.join(qaDir,`ui-test-${Date.now()}.sqlite3`)

export default defineConfig({
  testDir: './e2e',
  timeout: 90000,
  retries: 0,
  workers: 1,
  outputDir: './qa/test-results',
  reporter: [['list'], ['html', { outputFolder: './qa/report', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:8001',
    browserName: 'chromium',
    channel: 'chrome',
    headless: true,
    viewport: { width: 1440, height: 1050 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 15000,
  },
  webServer: {
    command: `"${python}" -m uvicorn backend.app:app --host 127.0.0.1 --port 8001`,
    url: 'http://127.0.0.1:8001/api/health',
    reuseExistingServer: false,
    env: { FLEET_DB: dbPath, FLEET_ADMIN_PASSWORD: 'Fleet-QA-Password-2026' },
  },
})
