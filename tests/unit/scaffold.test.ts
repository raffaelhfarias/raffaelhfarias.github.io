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

    expect(astroConfig).toContain("site: 'https://raffaelhfarias.github.io'");
    expect(astroConfig).toContain("output: 'static'");
  });
});
