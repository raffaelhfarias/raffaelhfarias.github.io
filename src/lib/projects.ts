import { getCollection, type CollectionEntry } from "astro:content";
import type { Locale } from "../i18n/locales";

type Project = CollectionEntry<"projects">;

export function selectPublishedProjects(
  entries: Project[],
  locale: Locale,
): Project[] {
  return entries.filter(
    ({ data }) =>
      data.locale === locale && data.publicationStatus === "published",
  );
}

export async function getFeaturedProjects(locale: Locale): Promise<Project[]> {
  return selectPublishedProjects(await getCollection("projects"), locale)
    .filter(({ data }) => data.featured)
    .slice(0, 3);
}
