import { defineConfig } from "@playwright/test";

// The tests get their own backend, dashboard and database, so they never touch
// the dev data on ports 8000 and 5173. The database is reseeded on every run.
const backend = "http://127.0.0.1:8001";

export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  use: { baseURL: "http://localhost:5174" },
  webServer: [
    {
      command:
        "uv run -m backend.seed && uv run -m uvicorn backend.main:app --port 8001",
      url: `${backend}/api/health`,
      env: { UNDERCOVER_DB: "e2e/undercover.db" },
    },
    {
      command: "npx vite dashboard --port 5174 --strictPort",
      url: "http://localhost:5174",
      env: { UNDERCOVER_API_URL: backend },
    },
  ],
});
