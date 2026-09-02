import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";

import { afterEach, describe, expect, test } from "vitest";

import { validateProductionContent } from "../../scripts/check-production-content.mjs";

const workspaces: string[] = [];
const featured = [
  "src/content/projects/pt/direct-sales.mdx",
  "src/content/projects/en/direct-sales.mdx",
  "src/content/projects/pt/accounting-reconciliation.mdx",
  "src/content/projects/en/accounting-reconciliation.mdx",
  "src/content/projects/pt/financial-documents.mdx",
  "src/content/projects/en/financial-documents.mdx",
];

async function fixture() {
  const workspace = await mkdtemp(join(tmpdir(), "portfolio-content-"));
  workspaces.push(workspace);
  for (const relative of [
    "src/pages/index.astro",
    "src/data/routes.ts",
    "src/assets/profile/raffael-henrique.webp",
    "public/images/social-preview.png",
    "public/favicon.svg",
    ...featured,
  ]) {
    const path = join(workspace, relative);
    await mkdir(join(path, ".."), { recursive: true });
    await writeFile(
      path,
      relative.includes("direct-") ||
        relative.includes("reconciliation") ||
        relative.includes("financial-")
        ? "featured: true\npublicationStatus: published\n"
        : "clean",
      "utf8",
    );
  }
  return workspace;
}

afterEach(async () => {
  await Promise.all(
    workspaces
      .splice(0)
      .map((path) => rm(path, { recursive: true, force: true })),
  );
});

describe("validateProductionContent", () => {
  test("accepts clean production content without generic résumé PDFs", async () => {
    expect(validateProductionContent(await fixture())).toEqual([]);
  });

  test.each(["TODO", "TBD", "XX h", "[DEMO]"])(
    "rejects the marker %s",
    async (marker) => {
      const workspace = await fixture();
      await writeFile(join(workspace, "src/pages/index.astro"), marker, "utf8");
      expect(validateProductionContent(workspace).join("\n")).toContain(
        "forbidden marker",
      );
    },
  );

  test("rejects missing required assets and generic CV links", async () => {
    const workspace = await fixture();
    await rm(join(workspace, "src/assets/profile/raffael-henrique.webp"));
    await writeFile(
      join(workspace, "src/pages/index.astro"),
      '<a href="/cv/resume.pdf">CV</a>',
      "utf8",
    );
    const violations = validateProductionContent(workspace).join("\n");
    expect(violations).toContain("required file missing");
    expect(violations).toContain("generic résumé link");
  });
});
