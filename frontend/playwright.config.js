import { defineConfig } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// The e2e suite starts its OWN backend (port 8001, throwaway database) and frontend (port 5174),
// so it never touches your real data and can run while your dev servers are open.
const API_PORT = 8001;
const WEB_PORT = 5174;
const PYTHON = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const DB_FILE = path.join(os.tmpdir(), "mindtrack_e2e.db");
const DB_URL = "sqlite:///" + DB_FILE.replace(/\\/g, "/");

// Start every run from an empty database (config is also loaded by workers, which have TEST_WORKER_INDEX).
if (!process.env.TEST_WORKER_INDEX) {
  for (const f of [DB_FILE, DB_FILE + "-journal"]) { try { fs.rmSync(f, { force: true }); } catch { /* ignore */ } }
}

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.js",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,             // tests share one database and build on each other, so run them in order
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "e2e-report" }]],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    screenshot: "on",
    trace: "retain-on-failure",
    // PW_CHANNEL=chrome (or msedge) uses the browser already installed on your computer instead of downloading one.
    channel: process.env.PW_CHANNEL || undefined,
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  },
  outputDir: "e2e-results",
  webServer: [
    {
      command: `${PYTHON} -m uvicorn app.main:app --port ${API_PORT}`,
      cwd: "../backend",
      url: `http://localhost:${API_PORT}/health`,
      timeout: 120_000,
      reuseExistingServer: false,
      env: { ...process.env, DATABASE_URL: DB_URL, ALLOW_BACKDATED_CHECKINS: "true" },
    },
    {
      command: `npx vite --port ${WEB_PORT} --strictPort`,
      url: `http://localhost:${WEB_PORT}`,
      timeout: 120_000,
      reuseExistingServer: false,
      env: { ...process.env, VITE_API_URL: `http://localhost:${API_PORT}` },
    },
  ],
});
