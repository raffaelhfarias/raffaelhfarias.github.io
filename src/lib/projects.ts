import { getCollection, type CollectionEntry } from "astro:content";
import type { Locale } from "../i18n/locales";

export type Project = CollectionEntry<"projects">;

export const projectCategories = [
  "data-engineering",
  "automation",
  "analytics",
] as const;

export type ProjectCategory = (typeof projectCategories)[number];

export const categorySegments: Record<
  Locale,
  Record<ProjectCategory, string>
> = {
  en: {
    "data-engineering": "data-engineering",
    automation: "automation",
    analytics: "analytics",
  },
  pt: {
    "data-engineering": "engenharia-de-dados",
    automation: "automacao",
    analytics: "analise-de-dados",
  },
};

export function categoryFromSegment(
  locale: Locale,
  segment: string,
): ProjectCategory | undefined {
  return projectCategories.find(
    (category) => categorySegments[locale][category] === segment,
  );
}

export function selectPublishedProjects(
  entries: Project[],
  locale: Locale,
): Project[] {
  return entries
    .filter(
      ({ data }) =>
        data.locale === locale && data.publicationStatus === "published",
    )
    .sort(
      (left, right) =>
        Number(right.data.featured) - Number(left.data.featured) ||
        right.data.publishedAt.getTime() - left.data.publishedAt.getTime(),
    );
}

export function findTranslation(
  entries: Project[],
  translationKey: string,
  locale: Locale,
): Project | undefined {
  return entries.find(
    ({ data }) =>
      data.locale === locale &&
      data.translationKey === translationKey &&
      data.publicationStatus === "published",
  );
}

export function groupByCategory(
  entries: Project[],
): Record<ProjectCategory, Project[]> {
  const groups: Record<ProjectCategory, Project[]> = {
    "data-engineering": [],
    automation: [],
    analytics: [],
  };

  for (const entry of entries) {
    groups[entry.data.category].push(entry);
  }

  return groups;
}

export async function getPublishedProjects(locale: Locale): Promise<Project[]> {
  return selectPublishedProjects(await getCollection("projects"), locale);
}

export async function getFeaturedProjects(locale: Locale): Promise<Project[]> {
  return (await getPublishedProjects(locale))
    .filter(({ data }) => data.featured)
    .slice(0, 3);
}
