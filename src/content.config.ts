import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";

import { articleSchema } from "./content/article-schema";
import { projectSchema } from "./content/project-schema";

const projects = defineCollection({
  loader: glob({
    base: "./src/content/projects",
    pattern: "**/*.{md,mdx}",
  }),
  schema: projectSchema,
});

const articles = defineCollection({
  loader: glob({
    base: "./src/content/articles",
    pattern: "**/*.{md,mdx}",
  }),
  schema: articleSchema,
});

export const collections = { projects, articles };
