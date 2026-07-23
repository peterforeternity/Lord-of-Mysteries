import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
  },
  webServer: [
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      port: 5173,
      cwd: ".",
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        VITE_API_BASE_URL: "http://127.0.0.1:8000",
      },
    },
  ],
});
