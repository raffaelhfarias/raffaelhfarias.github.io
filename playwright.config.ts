import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: { baseURL: "http://127.0.0.1:4321" },
  globalSetup: "./tests/e2e/global-setup.ts",
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "Pixel 7", use: { ...devices["Pixel 7"] } },
  ],
});
