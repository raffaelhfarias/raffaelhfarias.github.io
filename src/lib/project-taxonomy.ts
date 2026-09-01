import type { Locale } from "../i18n/locales";

export const projectTaxonomy = {
  "data-engineering": {
    label: { pt: "Engenharia de dados", en: "Data engineering" },
    segment: { pt: "engenharia-de-dados", en: "data-engineering" },
  },
  automation: {
    label: { pt: "Automação", en: "Automation" },
    segment: { pt: "automacao", en: "automation" },
  },
  analytics: {
    label: { pt: "Análise de dados", en: "Analytics" },
    segment: { pt: "analise-de-dados", en: "analytics" },
  },
} as const;

export type ProjectCategory = keyof typeof projectTaxonomy;
export const projectCategories = Object.keys(
  projectTaxonomy,
) as ProjectCategory[];

export const reservedProjectSegments = new Set([
  "all",
  ...projectCategories.flatMap((category) => [
    projectTaxonomy[category].segment.pt,
    projectTaxonomy[category].segment.en,
  ]),
]);

export function isReservedProjectSegment(segment: string): boolean {
  return reservedProjectSegments.has(segment);
}

export function categoryFromSegment(
  locale: Locale,
  segment: string,
): ProjectCategory | undefined {
  return projectCategories.find(
    (category) => projectTaxonomy[category].segment[locale] === segment,
  );
}

export function categorySegment(
  locale: Locale,
  category: ProjectCategory,
): string {
  return projectTaxonomy[category].segment[locale];
}

export function categoryLabel(
  locale: Locale,
  category: ProjectCategory,
): string {
  return projectTaxonomy[category].label[locale];
}
