import { describe, expect, it } from "vitest";
import { engineeringToolGroups } from "../../src/components/home/engineering-stack";

describe("engineeringToolGroups", () => {
  it("mantém as camadas técnicas nos dois idiomas", () => {
    expect(engineeringToolGroups.pt.map((group) => group.slug)).toEqual([
      "data",
      "automation",
      "integration",
      "infrastructure",
      "cloud",
    ]);
    expect(engineeringToolGroups.en).toHaveLength(5);
  });

  it("marca Azure como competência em aprofundamento", () => {
    const azure = engineeringToolGroups.pt
      .flatMap((group) => group.tools)
      .find((tool) => tool.slug === "azure");

    expect(azure?.status).toBe("in-depth");
  });

  it("não deixa ferramentas sem nome, função ou marca visual", () => {
    for (const group of engineeringToolGroups.pt) {
      for (const tool of group.tools) {
        expect(tool.name.length).toBeGreaterThan(0);
        expect(tool.role.length).toBeGreaterThan(0);
        expect(tool.logo.length).toBeGreaterThan(0);
      }
    }
  });
});
