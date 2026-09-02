import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const rootDirectory = fileURLToPath(new URL("../..", import.meta.url));

describe("Astro scaffold", () => {
  it("uses strict Astro TypeScript settings", async () => {
    const tsconfig = await readFile(`${rootDirectory}/tsconfig.json`, "utf8");

    expect(tsconfig).toContain("astro/tsconfigs/strict");
  });

  it("defines the production static site URL", async () => {
    const astroConfig = await readFile(
      `${rootDirectory}/astro.config.mjs`,
      "utf8",
    );

    expect(astroConfig).toMatch(
      /site:\s*["']https:\/\/raffaelhfarias\.github\.io["']/,
    );
    expect(astroConfig).toMatch(/output:\s*["']static["']/);
  });

  it("keeps every installed lockfile package versioned for npm ci", async () => {
    const lockfile = JSON.parse(
      await readFile(`${rootDirectory}/package-lock.json`, "utf8"),
    ) as {
      packages: Record<string, { link?: boolean; version?: string }>;
    };

    const invalidPackages = Object.entries(lockfile.packages)
      .filter(([path, metadata]) => path && !metadata.link && !metadata.version)
      .map(([path]) => path);

    expect(invalidPackages).toEqual([]);
  });
});
