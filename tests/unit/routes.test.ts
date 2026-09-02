import { describe, expect, it } from "vitest";

import { localizedPath, swapLocale } from "../../src/i18n/routes";

describe("localizedPath", () => {
  it("creates a Portuguese path for projects", () => {
    expect(localizedPath("pt", "projects")).toBe("/pt/projetos/");
  });

  it("creates a localized root path", () => {
    expect(localizedPath("en", "")).toBe("/en/");
  });
});

describe("swapLocale", () => {
  it("translates every recognized segment in a nested path", () => {
    expect(swapLocale("/pt/projetos/venda-direta/", "en")).toBe(
      "/en/projects/direct-sales/",
    );
  });
});
