import { z } from "astro/zod";

const nonEmptyString = z.string().trim().min(1);
const reservedProjectSegments = [
  "all",
  "data-engineering",
  "automation",
  "analytics",
  "automacao",
  "engenharia-de-dados",
  "analise-de-dados",
];

export const metricSchema = z.object({
  value: nonEmptyString,
  label: nonEmptyString,
  qualifier: nonEmptyString.optional(),
});

export const projectSchema = z
  .object({
    locale: z.enum(["pt", "en"]),
    translationKey: nonEmptyString,
    slug: nonEmptyString.refine(
      (slug) => !reservedProjectSegments.includes(slug),
      "Project slugs cannot use reserved listing segments.",
    ),
    title: nonEmptyString,
    summary: nonEmptyString,
    type: z.enum(["professional", "personal", "academic"]),
    role: nonEmptyString,
    period: nonEmptyString,
    publishedAt: z.coerce.date(),
    featured: z.boolean().default(false),
    publicationStatus: z.enum(["draft", "published"]),
    confidential: z.boolean().default(false),
    category: z.enum(["data-engineering", "automation", "analytics"]),
    skills: z.array(nonEmptyString).min(1),
    stack: z.array(nonEmptyString).min(1),
    metrics: z.array(metricSchema).default([]),
    cover: nonEmptyString,
    ogImage: nonEmptyString.optional(),
    repository: z.url().optional(),
    demo: z.url().optional(),
  })
  .refine(
    (project) =>
      !(
        project.featured &&
        project.publicationStatus === "published" &&
        project.metrics.length === 0
      ),
    {
      path: ["metrics"],
      message: "Featured published projects must include at least one metric.",
    },
  );
