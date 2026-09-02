import { describe, expect, it } from "vitest";

import {
  projectCategories,
  projectTaxonomy,
  reservedProjectSegments,
} from "../../src/lib/project-taxonomy";
import { projectSchema } from "../../src/content/project-schema";

const baseProject = {
  locale: "en",
  translationKey: "example",
  slug: "example",
  title: "Example",
  summary: "A publishable example project.",
  type: "professional",
  role: "Engineer",
  period: "2026",
  publishedAt: new Date("2026-01-01"),
  featured: false,
  publicationStatus: "published",
  confidential: false,
  category: "automation",
  skills: ["Automation"],
  stack: ["TypeScript"],
  metrics: [],
  cover: "/images/social-preview.png",
};

describe("project taxonomy", () => {
  it("keeps every localized category segment reserved from project slugs", () => {
    for (const slug of reservedProjectSegments) {
      expect(projectSchema.safeParse({ ...baseProject, slug }).success).toBe(
        false,
      );
    }
  });

  it("defines localized labels and segments for every category key", () => {
    expect(projectCategories).toEqual(Object.keys(projectTaxonomy));
    for (const category of projectCategories) {
      expect(projectTaxonomy[category].label.pt).not.toBe("");
      expect(projectTaxonomy[category].label.en).not.toBe("");
      expect(projectTaxonomy[category].segment.pt).not.toBe("");
      expect(projectTaxonomy[category].segment.en).not.toBe("");
    }
  });
});
