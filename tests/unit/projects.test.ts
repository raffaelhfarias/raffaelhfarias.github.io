import { describe, expect, it } from "vitest";
import type { CollectionEntry } from "astro:content";

import {
  findTranslation,
  groupByCategory,
  selectPublishedProjects,
} from "../../src/lib/projects";

type Project = CollectionEntry<"projects">;

function project(overrides: Record<string, unknown> = {}): Project {
  return {
    id: "projects/en/example",
    collection: "projects",
    data: {
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
      ...overrides,
    },
  } as Project;
}

describe("selectPublishedProjects", () => {
  it("excludes drafts and sorts featured projects before newest non-featured projects", () => {
    const projects = [
      project({ slug: "draft", publicationStatus: "draft" }),
      project({
        slug: "older-featured",
        featured: true,
        publishedAt: new Date("2025-01-01"),
      }),
      project({ slug: "newest", publishedAt: new Date("2026-03-01") }),
      project({
        slug: "newer-featured",
        featured: true,
        publishedAt: new Date("2026-02-01"),
      }),
      project({ slug: "pt", locale: "pt" }),
    ];

    expect(
      selectPublishedProjects(projects, "en").map(({ data }) => data.slug),
    ).toEqual(["newer-featured", "older-featured", "newest"]);
  });

  it("uses the slug as a deterministic tie-breaker for equally ranked projects", () => {
    const projects = [
      project({
        slug: "zebra",
        translationKey: "zebra",
        featured: true,
        publishedAt: new Date("2026-03-01"),
      }),
      project({
        slug: "alpha",
        translationKey: "alpha",
        featured: true,
        publishedAt: new Date("2026-03-01"),
      }),
      project({
        slug: "bravo",
        translationKey: "zulu",
        featured: true,
        publishedAt: new Date("2026-03-01"),
      }),
      project({
        slug: "bravo",
        translationKey: "bravo",
        featured: true,
        publishedAt: new Date("2026-03-01"),
      }),
    ];

    expect(
      selectPublishedProjects(projects, "en").map(({ data }) => data.slug),
    ).toEqual(["alpha", "bravo", "bravo", "zebra"]);
    expect(
      selectPublishedProjects(projects, "en").map(
        ({ data }) => data.translationKey,
      ),
    ).toEqual(["alpha", "bravo", "zulu", "zebra"]);
  });
});

describe("findTranslation", () => {
  it("returns the published localized translation", () => {
    const projects = [
      project({ translationKey: "same", locale: "en" }),
      project({ translationKey: "same", locale: "pt", slug: "mesmo" }),
    ];

    expect(findTranslation(projects, "same", "pt")?.data.slug).toBe("mesmo");
  });

  it("returns undefined when the localized translation is missing or a draft", () => {
    const projects = [
      project({
        translationKey: "draft-only",
        locale: "pt",
        publicationStatus: "draft",
      }),
    ];

    expect(findTranslation(projects, "draft-only", "en")).toBeUndefined();
    expect(findTranslation(projects, "draft-only", "pt")).toBeUndefined();
  });
});

describe("groupByCategory", () => {
  it("groups the supplied projects by machine-readable category", () => {
    const projects = [
      project({ slug: "automated", category: "automation" }),
      project({ slug: "warehouse", category: "data-engineering" }),
      project({ slug: "report", category: "analytics" }),
    ];

    const grouped = groupByCategory(projects);

    expect(grouped.automation.map(({ data }) => data.slug)).toEqual([
      "automated",
    ]);
    expect(grouped["data-engineering"].map(({ data }) => data.slug)).toEqual([
      "warehouse",
    ]);
    expect(grouped.analytics.map(({ data }) => data.slug)).toEqual(["report"]);
  });
});
