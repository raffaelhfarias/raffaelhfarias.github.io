import { z } from "astro/zod";

const nonEmptyString = z.string().trim().min(1);

export const articleSchema = z.object({
  locale: z.enum(["pt", "en"]),
  translationKey: nonEmptyString,
  slug: nonEmptyString,
  title: nonEmptyString,
  description: nonEmptyString,
  publishedAt: z.coerce.date(),
  tags: z.array(z.string()).default([]),
  publicationStatus: z.enum(["draft", "published"]),
});
