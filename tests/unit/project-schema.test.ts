import { describe, expect, it } from "vitest";

import { metricSchema, projectSchema } from "../../src/content/project-schema";

const baseProject = {
  locale: "pt",
  translationKey: "direct-sales",
  slug: "venda-direta",
  title: "Vendas diretas",
  summary: "Orquestração de processos para vendas diretas.",
  type: "professional",
  role: "Desenvolvedor de automação",
  publishedAt: new Date("2026-08-01"),
  featured: true,
  publicationStatus: "published",
  confidential: true,
  skills: ["orchestration"],
  stack: ["Python", "Kestra"],
  cover: "/images/projects/direct-sales.webp",
  metrics: [
    {
      value: "20–30 h",
      label: "economizadas por mês",
      qualifier: "faixa aproximada",
    },
  ],
};

describe("projectSchema", () => {
  it("exports a schema for project metrics", () => {
    const result = metricSchema.safeParse(baseProject.metrics[0]);

    expect(result.success).toBe(true);
  });

  it("accepts a measurable published featured project", () => {
    const result = projectSchema.safeParse(baseProject);

    expect(result.success).toBe(true);
  });

  it("rejects a featured published project without metrics", () => {
    const result = projectSchema.safeParse({ ...baseProject, metrics: [] });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues).toContainEqual(
        expect.objectContaining({ path: ["metrics"] }),
      );
    }
  });

  it("accepts a non-featured draft without metrics", () => {
    const result = projectSchema.safeParse({
      ...baseProject,
      featured: false,
      publicationStatus: "draft",
      metrics: [],
    });

    expect(result.success).toBe(true);
  });
});
