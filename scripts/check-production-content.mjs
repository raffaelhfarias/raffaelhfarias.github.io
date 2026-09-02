import { existsSync, readFileSync, readdirSync } from "node:fs";
import { extname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const roots = ["src/content", "src/data", "src/pages"];
const forbidden = [/\bTODO\b/, /\bTBD\b/, /\bXX\s*(?:h|%|k)\b/i, /\[DEMO\]/];
const requiredFiles = [
  "src/assets/profile/raffael-henrique.webp",
  "public/images/social-preview.png",
  "public/favicon.svg",
];
const featuredCases = [
  "src/content/projects/pt/direct-sales.mdx",
  "src/content/projects/en/direct-sales.mdx",
  "src/content/projects/pt/accounting-reconciliation.mdx",
  "src/content/projects/en/accounting-reconciliation.mdx",
  "src/content/projects/pt/financial-documents.mdx",
  "src/content/projects/en/financial-documents.mdx",
];

export function validateProductionContent(workspace = process.cwd()) {
  const violations = [];

  function walk(directory) {
    if (!existsSync(directory)) return;
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) walk(path);
      else if ([".astro", ".ts", ".md", ".mdx"].includes(extname(path))) {
        const value = readFileSync(path, "utf8");
        for (const pattern of forbidden) {
          if (pattern.test(value))
            violations.push(`${path}: forbidden marker ${pattern}`);
        }
        if (/\/cv\//i.test(value))
          violations.push(`${path}: generic résumé link is not allowed`);
      }
    }
  }

  for (const root of roots) walk(resolve(workspace, root));
  for (const file of requiredFiles) {
    if (!existsSync(resolve(workspace, file)))
      violations.push(`${file}: required file missing`);
  }
  for (const file of featuredCases) {
    const path = resolve(workspace, file);
    if (!existsSync(path)) violations.push(`${file}: featured case missing`);
    else {
      const value = readFileSync(path, "utf8");
      if (
        !/featured:\s*true/i.test(value) ||
        !/publicationStatus:\s*published/i.test(value)
      ) {
        violations.push(`${file}: featured case must be published`);
      }
    }
  }
  return violations;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
) {
  const violations = validateProductionContent();
  if (violations.length) {
    console.error(violations.join("\n"));
    process.exitCode = 1;
  } else {
    console.log("Production content validated");
  }
}
