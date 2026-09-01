import { z } from "astro/zod";
import {
  isReservedProjectSegment,
  projectCategories,
} from "../lib/project-taxonomy";

const nonEmptyString = z.string().trim().min(1);

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
      (slug) => !isReservedProjectSegment(slug),
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
    category: z.enum(projectCategories),
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
