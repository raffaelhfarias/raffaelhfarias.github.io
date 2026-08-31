# Data & Automation Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Jekyll blog with a bilingual, recruiter-first Astro portfolio that positions Raffael Henrique as a mid-level Data & Automation Engineer and proves that positioning through three measurable case studies.

**Architecture:** Astro generates a fully static site from validated local Markdown/MDX collections. Shared TypeScript modules own locale routing, content selection, publication rules, and legacy-route mapping; focused Astro components render the approved Editorial Engineering interface with minimal client JavaScript. GitHub Actions validates, tests, builds, and deploys the resulting `dist/` artifact to the existing user-site GitHub Pages domain.

**Tech Stack:** Astro, TypeScript strict mode, Astro Content Collections, MDX, CSS, Vitest, Playwright, axe-core, Lighthouse CI, npm, GitHub Actions, GitHub Pages.

---

## Preconditions

Execute this plan in an isolated git worktree created from commit `b03f9ef`. Do not remove the published Jekyll site until Task 12 passes its full verification gate.

Before Task 8 begins, obtain the following approved source materials from the portfolio owner:

- a public professional portrait in JPG or WebP;
- Portuguese and English PDF résumés;
- one verified metric for each featured case;
- sanitized architecture facts for each featured case;
- sanitized screenshots or an explicit decision to use an editorial diagram instead;
- a precise statement of personal responsibility for each featured case.

Record those facts in `docs/content-source/portfolio-materials.md`. Values may be exact or explicitly labeled ranges. Do not infer or invent business metrics.

## Planned file map

### Tooling and deployment

- `package.json` — npm scripts and dependency contract.
- `package-lock.json` — reproducible dependency resolution; must be committed.
- `astro.config.mjs` — static output, site URL, MDX, sitemap, and i18n.
- `tsconfig.json` — strict Astro TypeScript configuration.
- `vitest.config.ts` — unit-test configuration.
- `playwright.config.ts` — production-preview browser tests.
- `lighthouserc.json` — performance and quality budgets.
- `.github/workflows/pages-deploy.yml` — validation and Astro deployment.

### Domain and content

- `src/content.config.ts` — project and article collection definitions.
- `src/content/project-schema.ts` — reusable project schema and publication refinement.
- `src/content/article-schema.ts` — reusable article schema.
- `src/content/projects/{pt,en}/*.mdx` — localized project cases.
- `src/content/articles/{pt,en}/*.md` — localized editorial archive.
- `src/i18n/locales.ts` — locale types and UI messages.
- `src/i18n/routes.ts` — localized route construction and locale switching.
- `src/lib/projects.ts` — collection queries and translation pairing.
- `src/data/legacy-routes.ts` — old Jekyll slug compatibility map.

### UI

- `src/layouts/BaseLayout.astro` — document shell and shared metadata.
- `src/layouts/CaseLayout.astro` — case-study structure.
- `src/components/navigation/{Header,Footer}.astro` — global navigation.
- `src/components/seo/SeoHead.astro` — canonical, hreflang, Open Graph, and JSON-LD.
- `src/components/home/*.astro` — approved home sections.
- `src/components/projects/{ProjectCard,ProjectFilters}.astro` — project discovery.
- `src/components/cases/{ImpactMetrics,ArchitectureDiagram}.astro` — reusable case evidence.
- `src/styles/{tokens,global}.css` — Editorial Engineering design system.
- `src/pages/index.astro` — root-language redirect page.
- `src/pages/[lang]/index.astro` — localized home routes.
- `src/pages/pt/{projetos,sobre,artigos}/**` — Portuguese routes.
- `src/pages/en/{projects,about,articles}/**` — English routes.
- `src/pages/posts/[legacy].astro` — compatibility pages for existing URLs.
- `src/pages/404.astro` — bilingual recovery page.

### Tests and validation

- `tests/unit/*.test.ts` — pure routing, schema, query, and publication tests.
- `tests/e2e/*.spec.ts` — navigation, language, SEO, accessibility, and responsive tests.
- `scripts/check-production-content.mjs` — rejects demo markers and missing final assets.

## Task 1: Establish the Astro and test foundation

**Files:**

- Modify: `.gitignore`
- Create: `package.json`
- Create: `package-lock.json`
- Create: `astro.config.mjs`
- Create: `tsconfig.json`
- Create: `vitest.config.ts`
- Create: `playwright.config.ts`
- Create: `.prettierignore`
- Create: `tests/unit/scaffold.test.ts`
- Modify: `.devcontainer/devcontainer.json`
- Modify: `.devcontainer/post-create.sh`
- Modify: `.vscode/extensions.json`
- Modify: `.vscode/settings.json`
- Modify: `.vscode/tasks.json`

- [ ] **Step 1: Make npm artifacts trackable**

Remove `package-lock.json` from `.gitignore` and add generated directories:

```gitignore
# Astro and test outputs
node_modules/
.astro/
dist/
coverage/
playwright-report/
test-results/
.superpowers/
```

Create `.prettierignore` so formatting checks target the Astro implementation while the Jekyll source is still present:

```gitignore
node_modules/
.astro/
dist/
.superpowers/
docs/
_posts/
_tabs/
_data/
assets/
commons/
```

- [ ] **Step 2: Install the runtime and test dependencies**

Run:

```powershell
npm.cmd init -y
npm.cmd install astro @astrojs/mdx @astrojs/sitemap
npm.cmd install --save-dev typescript @astrojs/check vitest @playwright/test @axe-core/playwright @lhci/cli linkinator prettier prettier-plugin-astro
```

Expected: `package.json` and a tracked `package-lock.json` exist; npm exits with code 0.

- [ ] **Step 3: Add the failing scaffold test**

Create `tests/unit/scaffold.test.ts`:

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('Astro foundation', () => {
  it('uses strict TypeScript and the production site URL', () => {
    const tsconfig = readFileSync('tsconfig.json', 'utf8');
    const astroConfig = readFileSync('astro.config.mjs', 'utf8');

    expect(tsconfig).toContain('astro/tsconfigs/strict');
    expect(astroConfig).toContain("site: 'https://raffaelhfarias.github.io'");
    expect(astroConfig).toContain("output: 'static'");
  });
});
```

- [ ] **Step 4: Run the test and confirm the red state**

Run: `npx.cmd vitest run tests/unit/scaffold.test.ts`

Expected: FAIL because `astro.config.mjs` and `tsconfig.json` do not exist.

- [ ] **Step 5: Create the minimal Astro configuration**

Create `astro.config.mjs`:

```js
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://raffaelhfarias.github.io',
  output: 'static',
  trailingSlash: 'always',
  integrations: [mdx(), sitemap()],
  i18n: {
    defaultLocale: 'pt',
    locales: ['pt', 'en'],
    routing: { prefixDefaultLocale: true, redirectToDefaultLocale: false },
  },
});
```

Create `tsconfig.json`:

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": [".astro/types.d.ts", "**/*"],
  "exclude": ["dist"]
}
```

Create `vitest.config.ts`:

```ts
/// <reference types="vitest/config" />
import { getViteConfig } from 'astro/config';

export default getViteConfig({
  test: { include: ['tests/unit/**/*.test.ts'] },
});
```

Create `playwright.config.ts`:

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  webServer: {
    command: 'npm run preview -- --host 127.0.0.1',
    url: 'http://127.0.0.1:4321/pt/',
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
  use: { baseURL: 'http://127.0.0.1:4321' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
});
```

Replace the generated `scripts` in `package.json` with:

```json
{
  "scripts": {
    "dev": "astro dev",
    "build": "astro check && astro build",
    "preview": "astro preview",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "check:links": "linkinator dist --recurse --skip '^mailto:'",
    "check:content": "node scripts/check-production-content.mjs",
    "format:check": "prettier --check .",
    "verify": "npm run format:check && npm run test && npm run check:content && npm run build && npm run test:e2e && npm run check:links"
  },
  "type": "module"
}
```

Replace the Jekyll development-container image with Node 22 and make setup reproducible:

```json
{
  "name": "Astro Portfolio",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:22-bookworm",
  "postCreateCommand": "bash .devcontainer/post-create.sh",
  "customizations": {
    "vscode": {
      "extensions": ["astro-build.astro-vscode", "esbenp.prettier-vscode", "ms-playwright.playwright"]
    }
  }
}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
npm ci
npx playwright install --with-deps chromium
npm run build
```

Set `.vscode/extensions.json` to recommend `astro-build.astro-vscode`, `esbenp.prettier-vscode`, and `ms-playwright.playwright`. Remove Liquid associations from `.vscode/settings.json`. Replace `.vscode/tasks.json` with `npm run dev`, `npm run verify`, and `npm run test:e2e` shell tasks.

```json
{
  "version": "2.0.0",
  "tasks": [
    { "label": "Astro: dev", "type": "shell", "command": "npm run dev", "isBackground": true, "problemMatcher": [] },
    { "label": "Portfolio: verify", "type": "shell", "command": "npm run verify", "group": { "kind": "test", "isDefault": true }, "problemMatcher": [] },
    { "label": "Portfolio: e2e", "type": "shell", "command": "npm run test:e2e", "group": "test", "problemMatcher": [] }
  ]
}
```

- [ ] **Step 6: Verify the green state and commit**

Run: `npx.cmd vitest run tests/unit/scaffold.test.ts`

Expected: 1 test passes.

Run:

```powershell
git add .gitignore .prettierignore package.json package-lock.json astro.config.mjs tsconfig.json vitest.config.ts playwright.config.ts tests/unit/scaffold.test.ts .devcontainer .vscode
git commit -m "build: establish Astro test foundation"
```

## Task 2: Implement locale contracts and routing

**Files:**

- Create: `src/i18n/locales.ts`
- Create: `src/i18n/routes.ts`
- Create: `tests/unit/routes.test.ts`

- [ ] **Step 1: Write failing locale-route tests**

Create `tests/unit/routes.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { localizedPath, swapLocale } from '../../src/i18n/routes';

describe('localized routes', () => {
  it('builds prefixed routes with trailing slashes', () => {
    expect(localizedPath('pt', 'projects')).toBe('/pt/projetos/');
    expect(localizedPath('en', '')).toBe('/en/');
  });

  it('preserves the logical route when changing language', () => {
    expect(swapLocale('/pt/projetos/venda-direta/', 'en')).toBe('/en/projects/direct-sales/');
  });
});
```

- [ ] **Step 2: Run the focused test**

Run: `npx.cmd vitest run tests/unit/routes.test.ts`

Expected: FAIL because `src/i18n/routes.ts` does not exist.

- [ ] **Step 3: Implement locale messages and route aliases**

Create `src/i18n/locales.ts`:

```ts
export const locales = ['pt', 'en'] as const;
export type Locale = (typeof locales)[number];

export const ui = {
  pt: { projects: 'Projetos', about: 'Sobre', articles: 'Artigos', resume: 'Currículo' },
  en: { projects: 'Projects', about: 'About', articles: 'Articles', resume: 'Résumé' },
} satisfies Record<Locale, Record<string, string>>;

export function isLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}
```

Create `src/i18n/routes.ts`:

```ts
import type { Locale } from './locales';

const segmentAliases = {
  pt: { projects: 'projetos', about: 'sobre', articles: 'artigos', 'direct-sales': 'venda-direta' },
  en: { projects: 'projects', about: 'about', articles: 'articles', 'direct-sales': 'direct-sales' },
} as const;

export function localizedPath(locale: Locale, logicalPath = ''): string {
  const segments = logicalPath.split('/').filter(Boolean);
  const translated = segments.map((segment) => segmentAliases[locale][segment as keyof typeof segmentAliases.pt] ?? segment);
  return `/${locale}/${translated.join('/')}${translated.length ? '/' : ''}`;
}

export function swapLocale(pathname: string, target: Locale): string {
  const segments = pathname.split('/').filter(Boolean);
  const logical = segments.slice(1).map((segment) => {
    const match = Object.entries(segmentAliases.pt).find(([, value]) => value === segment)
      ?? Object.entries(segmentAliases.en).find(([, value]) => value === segment);
    return match?.[0] ?? segment;
  });
  return localizedPath(target, logical.join('/'));
}
```

- [ ] **Step 4: Run tests and commit**

Run: `npx.cmd vitest run tests/unit/routes.test.ts`

Expected: 2 tests pass.

```powershell
git add src/i18n tests/unit/routes.test.ts
git commit -m "feat: add bilingual route contracts"
```

## Task 3: Define and enforce the content model

**Files:**

- Create: `src/content/project-schema.ts`
- Create: `src/content/article-schema.ts`
- Create: `src/content.config.ts`
- Create: `tests/unit/project-schema.test.ts`

- [ ] **Step 1: Write failing publication-schema tests**

Create `tests/unit/project-schema.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { projectSchema } from '../../src/content/project-schema';

const baseProject = {
  locale: 'pt', translationKey: 'direct-sales', slug: 'venda-direta',
  title: 'Venda direta com autenticação resiliente', summary: 'Fluxo orquestrado e resiliente.',
  type: 'professional', role: 'Engenheiro de Dados e Automação', publishedAt: new Date('2026-05-21'),
  featured: true, publicationStatus: 'published', confidential: true,
  skills: ['orchestration'], stack: ['Python', 'Kestra'], cover: '/images/projects/direct-sales.webp',
  metrics: [{ value: '20–30 h', label: 'economizadas por mês', qualifier: 'faixa aproximada' }],
};

describe('projectSchema', () => {
  it('accepts a measurable published feature', () => {
    expect(projectSchema.safeParse(baseProject).success).toBe(true);
  });

  it('rejects a featured project without measurable evidence', () => {
    expect(projectSchema.safeParse({ ...baseProject, metrics: [] }).success).toBe(false);
  });

  it('allows an incomplete draft without publishing it', () => {
    expect(projectSchema.safeParse({ ...baseProject, featured: false, publicationStatus: 'draft', metrics: [] }).success).toBe(true);
  });
});
```

- [ ] **Step 2: Run the schema test**

Run: `npx.cmd vitest run tests/unit/project-schema.test.ts`

Expected: FAIL because the schema module does not exist.

- [ ] **Step 3: Implement the schemas and collections**

Create `src/content/project-schema.ts`:

```ts
import { z } from 'astro/zod';

export const metricSchema = z.object({
  value: z.string().min(1),
  label: z.string().min(1),
  qualifier: z.string().min(1).optional(),
});

export const projectSchema = z.object({
  locale: z.enum(['pt', 'en']),
  translationKey: z.string().min(1),
  slug: z.string().min(1),
  title: z.string().min(1),
  summary: z.string().min(1),
  type: z.enum(['professional', 'personal', 'academic']),
  role: z.string().min(1),
  publishedAt: z.coerce.date(),
  featured: z.boolean().default(false),
  publicationStatus: z.enum(['draft', 'published']),
  confidential: z.boolean().default(false),
  skills: z.array(z.string().min(1)).min(1),
  stack: z.array(z.string().min(1)).min(1),
  metrics: z.array(metricSchema).default([]),
  cover: z.string().min(1),
  ogImage: z.string().min(1).optional(),
  repository: z.string().url().optional(),
  demo: z.string().url().optional(),
}).superRefine((project, context) => {
  if (project.featured && project.publicationStatus === 'published' && project.metrics.length === 0) {
    context.addIssue({ code: 'custom', path: ['metrics'], message: 'Published featured projects require a metric.' });
  }
});
```

Create `src/content/article-schema.ts`:

```ts
import { z } from 'astro/zod';

export const articleSchema = z.object({
  locale: z.enum(['pt', 'en']),
  translationKey: z.string().min(1),
  slug: z.string().min(1),
  title: z.string().min(1),
  description: z.string().min(1),
  publishedAt: z.coerce.date(),
  tags: z.array(z.string()).default([]),
  publicationStatus: z.enum(['draft', 'published']),
});
```

Create `src/content.config.ts`:

```ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { articleSchema } from './content/article-schema';
import { projectSchema } from './content/project-schema';

const projects = defineCollection({
  loader: glob({ base: './src/content/projects', pattern: '**/*.{md,mdx}' }),
  schema: projectSchema,
});

const articles = defineCollection({
  loader: glob({ base: './src/content/articles', pattern: '**/*.{md,mdx}' }),
  schema: articleSchema,
});

export const collections = { projects, articles };
```

- [ ] **Step 4: Run tests and commit**

Run: `npx.cmd vitest run tests/unit/project-schema.test.ts`

Expected: 3 tests pass.

```powershell
git add src/content.config.ts src/content tests/unit/project-schema.test.ts
git commit -m "feat: validate portfolio content collections"
```

## Task 4: Build the Editorial Engineering shell

**Files:**

- Create: `src/styles/tokens.css`
- Create: `src/styles/global.css`
- Create: `src/components/navigation/Header.astro`
- Create: `src/components/navigation/Footer.astro`
- Create: `src/layouts/BaseLayout.astro`
- Create: `src/pages/[lang]/index.astro`
- Create: `tests/e2e/shell.spec.ts`

- [ ] **Step 1: Write the failing shell test**

Create `tests/e2e/shell.spec.ts`:

```ts
import { expect, test } from '@playwright/test';

test('renders the Portuguese recruiter-first shell', async ({ page }) => {
  await page.goto('/pt/');
  await expect(page.getByRole('banner')).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Principal' })).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR');
  await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
});
```

- [ ] **Step 2: Create the design tokens**

Create `src/styles/tokens.css`:

```css
:root {
  --paper: #f4f1e9;
  --surface: #fffdf8;
  --ink: #171717;
  --muted: #625f58;
  --line: #d6d0c3;
  --action: #164dcc;
  --action-contrast: #ffffff;
  --font-display: Georgia, 'Times New Roman', serif;
  --font-body: Inter, Arial, sans-serif;
  --font-mono: 'IBM Plex Mono', Consolas, monospace;
  --space-1: .5rem;
  --space-2: 1rem;
  --space-3: 1.5rem;
  --space-4: 2.5rem;
  --space-5: 4rem;
  --content: 72rem;
}
```

Create `src/styles/global.css` with reset, typography, focus, container, and reduced-motion rules:

```css
@import './tokens.css';
* { box-sizing: border-box; }
html { color: var(--ink); background: var(--paper); font-family: var(--font-body); }
body { margin: 0; line-height: 1.6; }
img { display: block; max-width: 100%; height: auto; }
a { color: inherit; }
:focus-visible { outline: 3px solid var(--action); outline-offset: 3px; }
.container { width: min(calc(100% - 2rem), var(--content)); margin-inline: auto; }
.eyebrow { color: var(--action); font: 700 .75rem/1 var(--font-mono); letter-spacing: .12em; text-transform: uppercase; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; animation: none !important; transition: none !important; } }
```

- [ ] **Step 3: Implement the semantic shell**

Create `src/components/navigation/Header.astro` and `Footer.astro` with localized links from `localizedPath()`. The header contract must be:

```astro
---
import type { Locale } from '../../i18n/locales';
import { ui } from '../../i18n/locales';
import { localizedPath } from '../../i18n/routes';
const { locale } = Astro.props as { locale: Locale };
---
<header>
  <div class="container header-inner">
    <a class="signature" href={localizedPath(locale)}>Raffael Henrique</a>
    <nav aria-label={locale === 'pt' ? 'Principal' : 'Primary'}>
      <a href={localizedPath(locale, 'projects')}>{ui[locale].projects}</a>
      <a href={localizedPath(locale, 'about')}>{ui[locale].about}</a>
      <a href={localizedPath(locale, 'articles')}>{ui[locale].articles}</a>
    </nav>
  </div>
</header>
```

Create `src/layouts/BaseLayout.astro` to import `global.css`, set `lang`, render a skip link, `Header`, one `<main id="main-content">`, and `Footer`.

```astro
---
import Header from '../components/navigation/Header.astro';
import Footer from '../components/navigation/Footer.astro';
import type { Locale } from '../i18n/locales';
import '../styles/global.css';

interface Props { locale: Locale; title: string; description: string; }
const { locale, title, description } = Astro.props;
---
<!doctype html>
<html lang={locale === 'pt' ? 'pt-BR' : 'en'}>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>{title}</title>
    <meta name="description" content={description} />
  </head>
  <body>
    <a class="skip-link" href="#main-content">{locale === 'pt' ? 'Ir para o conteúdo' : 'Skip to content'}</a>
    <Header locale={locale} />
    <main id="main-content"><slot /></main>
    <Footer locale={locale} />
  </body>
</html>
```

- [ ] **Step 4: Add the initial localized home route and run the E2E test**

Create `src/pages/[lang]/index.astro` with `getStaticPaths()` for `pt` and `en`, `BaseLayout`, and exactly one `<h1>`. Use the approved Portuguese and English positioning text, not demo markers.

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { isLocale, type Locale } from '../../i18n/locales';
export function getStaticPaths() { return [{ params: { lang: 'pt' } }, { params: { lang: 'en' } }]; }
const candidate = Astro.params.lang ?? '';
if (!isLocale(candidate)) throw new Error(`Unsupported locale: ${candidate}`);
const locale: Locale = candidate;
const copy = locale === 'pt'
  ? { title: 'Engenheiro de Dados e Automação — Raffael Henrique', description: 'Pipelines e automações confiáveis.', heading: 'Sistemas que transformam complexidade operacional em fluxo.' }
  : { title: 'Data & Automation Engineer — Raffael Henrique', description: 'Reliable data pipelines and automation.', heading: 'Systems that turn operational complexity into flow.' };
---
<BaseLayout locale={locale} title={copy.title} description={copy.description}>
  <h1>{copy.heading}</h1>
</BaseLayout>
```

Run:

```powershell
npm.cmd run build
npx.cmd playwright test tests/e2e/shell.spec.ts --project=desktop
```

Expected: build succeeds and 1 E2E test passes.

- [ ] **Step 5: Commit**

```powershell
git add src/styles src/components/navigation src/layouts src/pages tests/e2e/shell.spec.ts
git commit -m "feat: add editorial portfolio shell"
```

## Task 5: Add SEO, language alternates, and the root redirect

**Files:**

- Create: `src/components/seo/SeoHead.astro`
- Modify: `src/layouts/BaseLayout.astro`
- Create: `src/pages/index.astro`
- Create: `tests/e2e/seo.spec.ts`

- [ ] **Step 1: Write failing SEO tests**

Create `tests/e2e/seo.spec.ts`:

```ts
import { expect, test } from '@playwright/test';

test('home exposes localized SEO metadata', async ({ page }) => {
  await page.goto('/pt/');
  await expect(page).toHaveTitle(/Engenheiro de Dados e Automação.*Raffael Henrique/);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', 'https://raffaelhfarias.github.io/pt/');
  await expect(page.locator('link[hreflang="en"]')).toHaveAttribute('href', 'https://raffaelhfarias.github.io/en/');
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute('content', /social-preview/);
  await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(1);
});

test('root provides a static-host compatible Portuguese redirect', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('meta[http-equiv="refresh"]')).toHaveAttribute('content', '0;url=/pt/');
  await expect(page.getByRole('link', { name: 'Continuar em português' })).toHaveAttribute('href', '/pt/');
});
```

- [ ] **Step 2: Implement `SeoHead.astro`**

The component must accept localized title, description, canonical path, alternate path, image, locale, and JSON-LD. It must render canonical, `pt-BR`/`en` hreflang, Open Graph, Twitter card, and escaped JSON-LD via `set:html={JSON.stringify(jsonLd)}`.

```astro
---
import type { Locale } from '../../i18n/locales';
interface Props {
  title: string; description: string; canonicalPath: string; alternatePath: string;
  image: string; locale: Locale; jsonLd: Record<string, unknown>;
}
const { title, description, canonicalPath, alternatePath, image, locale, jsonLd } = Astro.props;
const origin = Astro.site ?? new URL('https://raffaelhfarias.github.io');
const canonical = new URL(canonicalPath, origin);
const alternate = new URL(alternatePath, origin);
const socialImage = new URL(image, origin);
---
<title>{title}</title>
<meta name="description" content={description} />
<link rel="canonical" href={canonical} />
<link rel="alternate" hreflang={locale === 'pt' ? 'en' : 'pt-BR'} href={alternate} />
<link rel="alternate" hreflang={locale === 'pt' ? 'pt-BR' : 'en'} href={canonical} />
<meta property="og:type" content="website" />
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:url" content={canonical} />
<meta property="og:image" content={socialImage} />
<meta name="twitter:card" content="summary_large_image" />
<script type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
```

- [ ] **Step 3: Connect SEO to `BaseLayout` and implement the root page**

Create `src/pages/index.astro`:

```astro
---
const destination = '/pt/';
---
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="refresh" content={`0;url=${destination}`} />
    <link rel="canonical" href="https://raffaelhfarias.github.io/pt/" />
    <title>Raffael Henrique — Engenheiro de Dados e Automação</title>
  </head>
  <body><a href={destination}>Continuar em português</a></body>
</html>
```

- [ ] **Step 4: Verify and commit**

Run: `npm.cmd run build`

Run: `npx.cmd playwright test tests/e2e/seo.spec.ts --project=desktop`

Expected: 2 tests pass.

```powershell
git add src/components/seo src/layouts/BaseLayout.astro src/pages/index.astro tests/e2e/seo.spec.ts
git commit -m "feat: add bilingual SEO metadata"
```

## Task 6: Implement the approved recruiter-first home

**Files:**

- Create: `src/components/home/Hero.astro`
- Create: `src/components/home/ImpactMetrics.astro`
- Create: `src/components/home/FeaturedCases.astro`
- Create: `src/components/home/WorkProcess.astro`
- Create: `src/components/home/SkillsEvidence.astro`
- Create: `src/components/home/ProfileSummary.astro`
- Create: `src/components/home/ContactCta.astro`
- Modify: `src/pages/[lang]/index.astro`
- Create: `tests/e2e/home.spec.ts`

- [ ] **Step 1: Write the failing home-structure test**

Create `tests/e2e/home.spec.ts`:

```ts
import { expect, test } from '@playwright/test';

test('home tells the recruiter story in the approved order', async ({ page }) => {
  await page.goto('/pt/');
  const main = page.getByRole('main');
  await expect(main.getByRole('heading', { name: 'Sistemas que transformam complexidade operacional em fluxo.' })).toBeVisible();
  await expect(main.getByRole('link', { name: 'Explorar cases' })).toHaveAttribute('href', '/pt/projetos/');
  await expect(main.locator('[data-section="hero"]')).toBeVisible();
  await expect(main.getByRole('heading', { name: 'Engenharia em produção' })).toBeVisible();
  await expect(main.getByRole('heading', { name: 'Como trabalho' })).toBeVisible();
  await expect(main.getByRole('heading', { name: 'Competências comprovadas' })).toBeVisible();
});
```

- [ ] **Step 2: Implement focused home components**

Each component receives typed props and owns one section only. `Hero.astro` must expose two CTAs; `ImpactMetrics.astro` accepts `Metric[]`; `FeaturedCases.astro` accepts at most three published project summaries; `WorkProcess.astro` renders the four approved stages; `SkillsEvidence.astro` links every skill group to a case; `ContactCta.astro` exposes LinkedIn, GitHub, e-mail, and résumé.

Use semantic section labels and no client-side hydration directives.

Implement `Hero.astro` with this complete contract:

```astro
---
interface Props {
  eyebrow: string; heading: string; summary: string;
  primary: { label: string; href: string };
  secondary: { label: string; href: string };
  availability: string; meta: string[];
}
const { eyebrow, heading, summary, primary, secondary, availability, meta } = Astro.props;
---
<section class="hero" data-section="hero">
  <div class="container hero-grid">
    <div>
      <p class="eyebrow">{eyebrow}</p>
      <h1>{heading}</h1>
      <p class="hero-summary">{summary}</p>
      <div class="hero-actions">
        <a class="button" href={primary.href}>{primary.label}</a>
        <a class="button button-secondary" href={secondary.href}>{secondary.label}</a>
      </div>
    </div>
    <aside aria-label={availability}>
      <strong>{availability}</strong>
      <ul>{meta.map((item) => <li>{item}</li>)}</ul>
    </aside>
  </div>
</section>
```

Use these exported prop contracts for the remaining files:

```ts
export interface Metric { value: string; label: string; qualifier?: string }
export interface FeaturedProject { title: string; summary: string; href: string; stack: string[]; metric: Metric }
export interface ProcessStep { index: string; title: string; description: string }
export interface SkillGroup { title: string; evidence: string; href: string }
export interface ContactLink { label: string; href: string; external?: boolean }
```

- [ ] **Step 3: Compose both localized homes**

Update `src/pages/[lang]/index.astro` to validate the locale, load published featured projects through `getFeaturedProjects(locale)`, and render sections in this exact order:

```astro
<Hero {...copy.hero} />
<ImpactMetrics metrics={aggregateMetrics} />
<FeaturedCases projects={featuredProjects} />
<WorkProcess steps={copy.process} />
<SkillsEvidence groups={copy.skillGroups} />
<ProfileSummary {...copy.profile} />
<ContactCta {...copy.contact} />
```

- [ ] **Step 4: Verify and commit**

Run: `npm.cmd run build`

Run: `npx.cmd playwright test tests/e2e/home.spec.ts`

Expected: desktop and mobile projects pass with no horizontal overflow.

```powershell
git add src/components/home src/pages/[lang]/index.astro tests/e2e/home.spec.ts
git commit -m "feat: build recruiter-first home"
```

## Task 7: Build project discovery and translation pairing

**Files:**

- Create: `src/lib/projects.ts`
- Create: `src/components/projects/ProjectCard.astro`
- Create: `src/components/projects/ProjectFilters.astro`
- Create: `src/pages/en/projects/index.astro`
- Create: `src/pages/en/projects/[category].astro`
- Create: `src/pages/pt/projetos/index.astro`
- Create: `src/pages/pt/projetos/[category].astro`
- Create: `tests/unit/projects.test.ts`
- Create: `tests/e2e/projects.spec.ts`

- [ ] **Step 1: Write failing project-query tests**

Create `tests/unit/projects.test.ts` with fixture entries and assertions that drafts are excluded, featured items sort first, and a missing translation is represented as unavailable rather than silently falling back.

The expected contract is:

```ts
expect(selectPublishedProjects(entries, 'pt').map((entry) => entry.data.slug)).toEqual(['venda-direta', 'airbnb']);
expect(findTranslation(entries, 'direct-sales', 'en')?.data.slug).toBe('direct-sales');
expect(findTranslation(entries, 'legacy-only', 'en')).toBeUndefined();
```

- [ ] **Step 2: Implement `src/lib/projects.ts`**

Export `selectPublishedProjects`, `getFeaturedProjects`, `findTranslation`, and `groupByCategory`. Pure selection functions accept entry arrays so Vitest can cover them; collection-loading wrappers call `getCollection('projects')`.

```ts
import { getCollection, type CollectionEntry } from 'astro:content';
import type { Locale } from '../i18n/locales';

type Project = CollectionEntry<'projects'>;

export function selectPublishedProjects(entries: Project[], locale: Locale): Project[] {
  return entries
    .filter(({ data }) => data.locale === locale && data.publicationStatus === 'published')
    .sort((a, b) => Number(b.data.featured) - Number(a.data.featured) || b.data.publishedAt.valueOf() - a.data.publishedAt.valueOf());
}

export function findTranslation(entries: Project[], translationKey: string, locale: Locale): Project | undefined {
  return entries.find(({ data }) => data.translationKey === translationKey && data.locale === locale && data.publicationStatus === 'published');
}

export function groupByCategory(entries: Project[]): Map<string, Project[]> {
  return entries.reduce((groups, entry) => {
    for (const skill of entry.data.skills) groups.set(skill, [...(groups.get(skill) ?? []), entry]);
    return groups;
  }, new Map<string, Project[]>());
}

export async function getFeaturedProjects(locale: Locale): Promise<Project[]> {
  return selectPublishedProjects(await getCollection('projects'), locale).filter(({ data }) => data.featured).slice(0, 3);
}
```

- [ ] **Step 3: Implement static filter routes**

`ProjectFilters.astro` renders ordinary links to `all`, `data-engineering`, `automation`, and `analytics` routes. The unfiltered page remains fully useful without JavaScript. Category pages use `getStaticPaths()` and filter at build time; no client framework is added.

```astro
---
interface Props { active: string; filters: Array<{ key: string; label: string; href: string }> }
const { active, filters } = Astro.props;
---
<nav aria-label="Filtros de projetos">
  <ul class="filters">
    {filters.map((filter) => (
      <li><a href={filter.href} aria-current={filter.key === active ? 'page' : undefined}>{filter.label}</a></li>
    ))}
  </ul>
</nav>
```

- [ ] **Step 4: Add E2E coverage**

Create `tests/e2e/projects.spec.ts` to verify:

```ts
test('filters are ordinary navigable links', async ({ page }) => {
  await page.goto('/pt/projetos/');
  await page.getByRole('link', { name: 'Automação' }).click();
  await expect(page).toHaveURL('/pt/projetos/automacao/');
  await expect(page.locator('article')).not.toHaveCount(0);
});
```

- [ ] **Step 5: Verify and commit**

Run: `npm.cmd run test -- tests/unit/projects.test.ts`

Run: `npm.cmd run build && npx.cmd playwright test tests/e2e/projects.spec.ts`

Expected: unit test and both browser projects pass.

```powershell
git add src/lib/projects.ts src/components/projects src/pages/pt/projetos src/pages/en/projects tests/unit/projects.test.ts tests/e2e/projects.spec.ts
git commit -m "feat: add static project discovery"
```

## Task 8: Create the case-study template and featured content

**Files:**

- Create: `docs/content-source/portfolio-materials.md`
- Create: `src/layouts/CaseLayout.astro`
- Create: `src/components/cases/ImpactMetrics.astro`
- Create: `src/components/cases/ArchitectureDiagram.astro`
- Create: `src/pages/en/projects/[slug].astro`
- Create: `src/pages/pt/projetos/[slug].astro`
- Create: `src/content/projects/{pt,en}/direct-sales.mdx`
- Create: `src/content/projects/{pt,en}/accounting-reconciliation.mdx`
- Create: `src/content/projects/{pt,en}/financial-documents.mdx`
- Create: `tests/e2e/cases.spec.ts`

- [ ] **Step 1: Complete and approve the source packet**

Create `docs/content-source/portfolio-materials.md` with six fixed sections per case: business context, personal responsibility, architecture nodes and edges, reliability decisions, verified metric with qualifier, and publishable evidence. Attach the portrait and résumé filenames in the same document. Ask the owner to approve this source packet before transcribing it.

- [ ] **Step 2: Write the failing case test**

Create `tests/e2e/cases.spec.ts`:

```ts
import { expect, test } from '@playwright/test';

test('featured case proves responsibility, architecture, reliability, and impact', async ({ page }) => {
  await page.goto('/pt/projetos/venda-direta/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(/Venda direta/);
  for (const heading of ['Minha responsabilidade', 'Arquitetura', 'Decisões técnicas', 'Confiabilidade', 'Resultados', 'Aprendizados']) {
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
  }
  await expect(page.locator('[data-metric]')).not.toHaveCount(0);
  await expect(page.locator('figure').getByRole('img')).toHaveAttribute('aria-label');
});
```

- [ ] **Step 3: Implement the reusable case layout**

`CaseLayout.astro` renders the executive summary, role, timeframe, metrics, an MDX slot, related case links, and localized SEO. `ArchitectureDiagram.astro` receives typed `nodes` and `edges`, renders a visual grid, and includes an adjacent textual ordered list so the architecture remains understandable without graphics.

The page route uses the collection entry, not pathname inference:

```astro
---
import { getCollection, render } from 'astro:content';
import CaseLayout from '../../../layouts/CaseLayout.astro';

export async function getStaticPaths() {
  const entries = await getCollection('projects', ({ data }) => data.locale === 'pt' && data.publicationStatus === 'published');
  return entries.map((entry) => ({ params: { slug: entry.data.slug }, props: { entry } }));
}

const { entry } = Astro.props;
const { Content, headings } = await render(entry);
---
<CaseLayout entry={entry} headings={headings} locale="pt">
  <Content />
</CaseLayout>
```

The English route is identical except for the locale filter and `locale="en"`. `CaseLayout.astro` must render the measurable evidence before the MDX body:

```astro
---
import ImpactMetrics from '../components/cases/ImpactMetrics.astro';
const { entry, locale } = Astro.props;
---
<article>
  <header class="case-header container">
    <p class="eyebrow">{entry.data.role}</p>
    <h1>{entry.data.title}</h1>
    <p>{entry.data.summary}</p>
    <ImpactMetrics metrics={entry.data.metrics} />
  </header>
  <div class="case-body container"><slot /></div>
</article>
```

- [ ] **Step 4: Transcribe the three approved cases in both languages**

Every file must use values from `docs/content-source/portfolio-materials.md`. Each published featured entry must include at least one metric and the required headings. English must be adapted for international recruiting terminology, not mechanically translated. No client, credential, private endpoint, personal data, or internal identifier may appear.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
npm.cmd run test
npm.cmd run build
npx.cmd playwright test tests/e2e/cases.spec.ts
```

Expected: all unit tests pass, build succeeds, and both case E2E projects pass.

```powershell
git add docs/content-source src/layouts/CaseLayout.astro src/components/cases src/pages/pt/projetos src/pages/en/projects src/content/projects tests/e2e/cases.spec.ts
git commit -m "feat: publish featured engineering cases"
```

## Task 9: Add About, articles, résumé, and profile assets

**Files:**

- Create: `src/pages/pt/sobre.astro`
- Create: `src/pages/en/about.astro`
- Create: `src/pages/pt/artigos/index.astro`
- Create: `src/pages/en/articles/index.astro`
- Create: `src/pages/pt/artigos/[slug].astro`
- Create: `src/pages/en/articles/[slug].astro`
- Create: `src/content/articles/{pt,en}/*`
- Create: `src/assets/profile/raffael-henrique.webp`
- Create: `public/cv/raffael-henrique-pt.pdf`
- Create: `public/cv/raffael-henrique-en.pdf`
- Create: `public/images/social-preview.png`
- Create: `public/favicon.svg`
- Create: `tests/e2e/about-and-articles.spec.ts`

- [ ] **Step 1: Write failing About and article smoke tests**

Test both locales for one `h1`, the professional portrait alt text, local résumé links, GitHub, LinkedIn, e-mail, and one migrated article.

- [ ] **Step 2: Build the localized About pages**

Use the approved mid-level positioning. Organize the page into profile, operating principles, evidence-linked capabilities, career trajectory, education, and contact. Do not use skill bars, badges, or the old generic illustration.

Both pages use the same semantic structure and localized copy:

```astro
<BaseLayout locale={locale} title={copy.title} description={copy.description}>
  <article class="container profile">
    <header><p class="eyebrow">{copy.eyebrow}</p><h1>{copy.heading}</h1><p>{copy.introduction}</p></header>
    <Image src={portrait} alt={copy.portraitAlt} widths={[320, 640]} sizes="(max-width: 48rem) 80vw, 24rem" />
    <section aria-labelledby="principles"><h2 id="principles">{copy.principlesTitle}</h2><ul>{copy.principles.map((item) => <li>{item}</li>)}</ul></section>
    <section aria-labelledby="trajectory"><h2 id="trajectory">{copy.trajectoryTitle}</h2><ol>{copy.trajectory.map((item) => <li><strong>{item.title}</strong><p>{item.description}</p></li>)}</ol></section>
    <nav aria-label={copy.contactLabel}>{copy.contacts.map((item) => <a href={item.href}>{item.label}</a>)}</nav>
  </article>
</BaseLayout>
```

- [ ] **Step 3: Migrate the editorial archive**

Move existing analytical posts into the article collection. Preserve original dates and source links. Mark articles without an English version as Portuguese-only so the language switch is omitted on those pages rather than falling back silently.

Each migrated article uses this frontmatter contract with its actual source values:

```yaml
locale: pt
translationKey: churn-prediction
slug: churn-prediction
title: Analisando a Taxa de Churn
description: Estudo de classificação aplicado à retenção de clientes.
publishedAt: 2025-03-27
tags: [Python, Machine Learning, Classificação]
publicationStatus: published
```

- [ ] **Step 4: Add final assets and verify**

Optimize the approved portrait to WebP while retaining the source outside the public build. Copy the approved PDFs to `public/cv/`. Run the E2E test and manually open both PDFs from the built preview.

Export a 1200×630 Editorial Engineering social card to `public/images/social-preview.png` and a high-contrast monogram to `public/favicon.svg`. The social card must contain the name, role, and short positioning line at a size readable in link previews.

- [ ] **Step 5: Commit**

```powershell
git add src/pages src/content/articles src/assets/profile public/cv tests/e2e/about-and-articles.spec.ts
git commit -m "feat: add bilingual profile and articles"
```

## Task 10: Migrate the existing project catalog and preserve old URLs

**Files:**

- Create: `src/data/legacy-routes.ts`
- Create: `src/pages/posts/[legacy].astro`
- Create: `src/components/seo/CompatibilityPage.astro`
- Create: localized catalog entries under `src/content/projects/pt/` and `src/content/projects/en/` for the twelve non-featured projects
- Create: `tests/unit/legacy-routes.test.ts`
- Create: `tests/e2e/legacy-routes.spec.ts`

- [ ] **Step 1: Write the legacy-map test**

The unit test must assert that all 15 current Jekyll slugs exist in `legacyRoutes`, every destination begins with `/pt/`, and destinations are unique where the source content is unique.

- [ ] **Step 2: Define the complete route map**

Create one explicit mapping per current post, for example:

```ts
export const legacyRoutes = {
  'Churn-Prediction': '/pt/projetos/churn-prediction/',
  'Cine-Match': '/pt/projetos/cine-match/',
  'Dados-Airbnb': '/pt/projetos/airbnb-veneza/',
  'Panorama-COVID-19': '/pt/projetos/panorama-covid-19/',
  'Gasolina-Preco': '/pt/projetos/preco-gasolina-brasil/',
  'Tensões-Comerciais-EUA-China-e-Impactos-no-Brasil': '/pt/projetos/tensoes-comerciais/',
  'whatsapp-sender': '/pt/projetos/metas-resultados-whatsapp/',
  'banco-de-horas': '/pt/projetos/banco-de-horas/',
  'aniversariantes-whatsapp': '/pt/projetos/aniversariantes-whatsapp/',
  'auditorias-vidibr': '/pt/projetos/auditorias-vidibr/',
  'baixas-financeiras-google-drive': '/pt/projetos/baixas-financeiras/',
  'resultados-venda-direta-browserless': '/pt/projetos/venda-direta/',
  'relatorio-iaf-trimestral': '/pt/projetos/relatorio-iaf/',
  'recebimentos-e-pagamentos': '/pt/projetos/conciliacao-contabil/',
  'folha-pagamento-via-whatsapp': '/pt/projetos/documentos-financeiros/',
} as const;
```

The key must match the decoded currently published path segment exactly, including capitalization. Astro will percent-encode non-ASCII characters in the generated URL.

- [ ] **Step 3: Generate static compatibility pages**

Because GitHub Pages cannot emit application-level HTTP 301 responses, preserve every old URL with a small static page containing canonical metadata, an immediate meta refresh, and a visible destination link. This satisfies the requirement that old URLs continue to work without introducing a backend.

Create `src/pages/posts/[legacy].astro`:

```astro
---
import CompatibilityPage from '../../components/seo/CompatibilityPage.astro';
import { legacyRoutes } from '../../data/legacy-routes';
export function getStaticPaths() {
  return Object.entries(legacyRoutes).map(([legacy, destination]) => ({ params: { legacy }, props: { destination } }));
}
const { destination } = Astro.props;
---
<CompatibilityPage destination={destination} />
```

Create `CompatibilityPage.astro`:

```astro
---
const { destination } = Astro.props as { destination: string };
const canonical = new URL(destination, Astro.site);
---
<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" /><meta http-equiv="refresh" content={`0;url=${destination}`} /><link rel="canonical" href={canonical} /><title>Conteúdo movido</title></head>
<body><p>Este conteúdo foi movido. <a href={destination}>Abrir a nova página</a>.</p></body></html>
```

- [ ] **Step 4: Migrate the twelve non-featured project summaries**

Normalize titles, summaries, role, stack, and skills from the current posts. Academic projects must use `type: academic` and `featured: false`. Professional projects without verified metrics may be published in the catalog but cannot be featured.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
npm.cmd run test -- tests/unit/legacy-routes.test.ts
npm.cmd run build
npx.cmd playwright test tests/e2e/legacy-routes.spec.ts
```

Expected: all 15 old URLs resolve to a compatibility page and target a built destination.

```powershell
git add src/data src/pages/posts src/components/seo/CompatibilityPage.astro src/content/projects tests/unit/legacy-routes.test.ts tests/e2e/legacy-routes.spec.ts
git commit -m "feat: migrate catalog and preserve legacy URLs"
```

## Task 11: Enforce production content, accessibility, responsiveness, and budgets

**Files:**

- Create: `scripts/check-production-content.mjs`
- Create: `tests/unit/production-content.test.ts`
- Create: `tests/e2e/accessibility.spec.ts`
- Create: `tests/e2e/responsive.spec.ts`
- Create: `src/pages/404.astro`
- Create: `lighthouserc.json`

- [ ] **Step 1: Write the failing production-content test**

Test that the validator rejects `TODO`, `TBD`, `XX h`, `[DEMO]`, missing portrait, or missing résumé files, and accepts a clean fixture tree.

- [ ] **Step 2: Implement the production-content validator**

`scripts/check-production-content.mjs` recursively scans `src/content`, `src/data`, and `src/pages`; rejects the exact demo-marker patterns; verifies the three featured cases in both locales; and verifies:

```js
const requiredFiles = [
  'src/assets/profile/raffael-henrique.webp',
  'public/cv/raffael-henrique-pt.pdf',
  'public/cv/raffael-henrique-en.pdf',
  'public/images/social-preview.png',
  'public/favicon.svg',
];
```

Exit 1 with one line per violation and exit 0 with `Production content validated`.

```js
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { extname, join } from 'node:path';

const roots = ['src/content', 'src/data', 'src/pages'];
const forbidden = [/\bTODO\b/i, /\bTBD\b/i, /\bXX\s*(?:h|%|k)\b/i, /\[DEMO\]/i];
const requiredFiles = ['src/assets/profile/raffael-henrique.webp', 'public/cv/raffael-henrique-pt.pdf', 'public/cv/raffael-henrique-en.pdf', 'public/images/social-preview.png', 'public/favicon.svg'];
const violations = [];

function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) walk(path);
    else if (['.astro', '.ts', '.md', '.mdx'].includes(extname(path))) {
      const value = readFileSync(path, 'utf8');
      for (const pattern of forbidden) if (pattern.test(value)) violations.push(`${path}: forbidden marker ${pattern}`);
    }
  }
}

for (const root of roots) walk(root);
for (const file of requiredFiles) if (!existsSync(file)) violations.push(`${file}: required file missing`);
if (violations.length) { console.error(violations.join('\n')); process.exit(1); }
console.log('Production content validated');
```

- [ ] **Step 3: Add accessibility and responsive E2E tests**

Use `@axe-core/playwright` on Home, Projects, one Case, About, and 404 in both locales. Assert zero serious or critical violations, no horizontal overflow at 390 px, visible keyboard focus, and one `h1` per page. Treat WCAG 2.2 AA as the manual and automated acceptance baseline.

- [ ] **Step 4: Implement the bilingual 404 page**

Show Portuguese and English recovery copy with links to `/pt/`, `/en/`, and both project indexes. Keep it static and usable without JavaScript.

```astro
---
import '../styles/global.css';
---
<!doctype html>
<html lang="pt-BR">
  <head><meta charset="utf-8" /><meta name="viewport" content="width=device-width" /><meta name="robots" content="noindex" /><title>404 — Página não encontrada</title></head>
  <body><main class="container"><h1>404</h1><p>Página não encontrada · Page not found</p><nav aria-label="Recovery"><a href="/pt/">Início</a> <a href="/pt/projetos/">Projetos</a> <a href="/en/">Home</a> <a href="/en/projects/">Projects</a></nav></main></body>
</html>
```

- [ ] **Step 5: Add Lighthouse budgets**

Create `lighthouserc.json`:

```json
{
  "ci": {
    "collect": {
      "staticDistDir": "./dist",
      "url": ["http://localhost/pt/", "http://localhost/pt/projetos/", "http://localhost/en/"]
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["error", { "minScore": 0.9 }]
      }
    }
  }
}
```

- [ ] **Step 6: Verify and commit**

Run:

```powershell
npm.cmd run check:content
npm.cmd run test
npm.cmd run build
npm.cmd run test:e2e
npx.cmd lhci autorun
```

Expected: content validator exits 0, all tests pass, and every Lighthouse category meets 0.90.

```powershell
git add scripts tests src/pages/404.astro lighthouserc.json
git commit -m "test: enforce portfolio quality gates"
```

## Task 12: Replace the Jekyll deployment and remove obsolete runtime files

**Files:**

- Modify: `.github/workflows/pages-deploy.yml`
- Delete: `Gemfile`
- Delete: `_config.yml`
- Delete: `_data/`
- Delete: `_plugins/`
- Delete: `_posts/`
- Delete: `_tabs/`
- Delete: `index.html`
- Delete: `.nojekyll`
- Delete: `tools/run.sh`
- Delete: `tools/test.sh`
- Delete: `.gitmodules`
- Remove submodule: `assets/lib`
- Delete after asset migration: `commons/avatar.jpg`
- Delete after asset migration: `assets/img/posts/covers/`
- Delete after replacement: `assets/img/favicons/`
- Preserve or relocate: `LICENSE`, branding source files, and migrated media.

- [ ] **Step 1: Run the full verification before deleting Jekyll**

Run: `npm.cmd run verify`

Expected: all checks pass. Stop if any command fails.

- [ ] **Step 2: Replace the workflow with the official Astro action**

Replace `.github/workflows/pages-deploy.yml` with:

```yaml
name: Build, verify, and deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run verify
      - run: npx lhci autorun

  build:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: withastro/action@v5

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

The dedicated `quality` job verifies the production build before the official Astro action creates the deployment artifact.

- [ ] **Step 3: Remove obsolete Jekyll runtime files**

Delete only the files listed in this task after confirming every post and asset has a new destination. Remove the `assets/lib` submodule with `git rm`, and preserve branding documentation under `docs/branding/` when it remains useful.

- [ ] **Step 4: Run the clean-room verification**

From a clean worktree or after deleting `node_modules` and reinstalling:

```powershell
npm.cmd ci
npx.cmd playwright install chromium
npm.cmd run verify
git diff --check
git status --short
```

Expected: install exits 0; all verification commands pass; `git diff --check` prints nothing; status contains only intended migration changes.

- [ ] **Step 5: Commit the runtime cutover**

```powershell
git add -A
git commit -m "build: replace Jekyll with Astro portfolio"
```

## Task 13: Final visual, confidentiality, and launch audit

**Files:**

- Modify: `src/styles/global.css` when the visual or responsive audit finds a shared defect.
- Modify: `src/components/navigation/Header.astro` or `src/components/navigation/Footer.astro` when the navigation audit finds a defect.
- Modify: the exact file under `src/components/home/`, `src/components/projects/`, or `src/components/cases/` named by a failing test.
- Modify: the exact localized entry under `src/content/projects/` or `src/content/articles/` named by the confidentiality audit.
- Update: `docs/content-source/portfolio-materials.md` with final approval status.

- [ ] **Step 1: Review every public route in both locales**

Check desktop and 390 px mobile layouts for Home, Projects, three featured cases, About, Articles, and 404. Verify typography, focus, spacing, diagram readability, image crops, and absence of horizontal overflow.

- [ ] **Step 2: Run the confidentiality checklist**

Search the built output for company names, internal system names, credentials, tokens, private hosts, personal data, and source-packet notes. Compare every case against the approved sanitization section in `docs/content-source/portfolio-materials.md`.

- [ ] **Step 3: Verify external actions**

Open both résumés, GitHub, LinkedIn, and the mailto link from the production preview. Confirm social preview images at 1200×630 and validate JSON-LD with a structured-data validator.

- [ ] **Step 4: Run the final gate**

Run:

```powershell
npm.cmd ci
npm.cmd run verify
npx.cmd lhci autorun
git diff --check
```

Expected: every command exits 0; all Lighthouse scores meet the approved threshold.

- [ ] **Step 5: Commit audit fixes**

```powershell
git add -A
git commit -m "chore: complete portfolio launch audit"
```

Do not push or switch GitHub Pages to the new workflow until the portfolio owner has reviewed the production preview and explicitly approved publication.

## Reference documentation

- Astro content collections: https://docs.astro.build/en/guides/content-collections/
- Astro internationalization: https://docs.astro.build/en/guides/internationalization/
- Astro testing: https://docs.astro.build/en/guides/testing/
- Astro GitHub Pages deployment: https://docs.astro.build/en/guides/deploy/github/
