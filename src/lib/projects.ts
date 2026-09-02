import { getCollection, type CollectionEntry } from "astro:content";
import type { Locale } from "../i18n/locales";
import { projectCategories, type ProjectCategory } from "./project-taxonomy";

export {
  categoryFromSegment,
  categoryLabel,
  categorySegment,
  projectCategories,
  projectTaxonomy,
  reservedProjectSegments,
  type ProjectCategory,
} from "./project-taxonomy";

export type Project = CollectionEntry<"projects">;

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
        right.data.publishedAt.getTime() - left.data.publishedAt.getTime() ||
        left.data.slug.localeCompare(right.data.slug) ||
        left.data.translationKey.localeCompare(right.data.translationKey),
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
  const groups = {} as Record<ProjectCategory, Project[]>;

  for (const category of projectCategories) groups[category] = [];

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
