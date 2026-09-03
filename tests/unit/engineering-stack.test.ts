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
        expect((tool.logo ?? tool.mark)?.length).toBeGreaterThan(0);
      }
    }
  });

  it("usa os ícones fornecidos pelo proprietário e reserva EA para Evolution API", () => {
    const tools = engineeringToolGroups.pt.flatMap((group) => group.tools);
    const findTool = (slug: string) => tools.find((tool) => tool.slug === slug);

    expect(findTool("python")?.logo).toBe("/assets/img/stacks/python.svg");
    expect(findTool("sql")?.logo).toBe(
      "/assets/img/stacks/azure-sql-server.svg",
    );
    expect(findTool("rest-webhooks")?.logo).toBe(
      "/assets/img/stacks/webhookd.svg",
    );
    expect(findTool("evolution-api")?.logo).toBeUndefined();
    expect(findTool("evolution-api")?.mark).toBe("EA");
  });
});
