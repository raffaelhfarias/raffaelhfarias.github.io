# Stack de engenharia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o bloco vazio de impacto por uma faixa bilíngue, acessível e visual de ferramentas organizadas por camadas de competência.

**Architecture:** Um catálogo tipado de ferramentas ficará separado do componente Astro. `EngineeringStack.astro` será responsável apenas pela apresentação, usando uma faixa CSS duplicada para o loop visual. A página `[lang]/index.astro` fornecerá os textos localizados e continuará posicionando os cases logo depois da stack.

**Tech Stack:** Astro, TypeScript, CSS puro, SVG local, Vitest e Playwright.

---

### Task 1: Criar catálogo tipado de ferramentas e testes de conteúdo

**Files:**
- Create: `src/components/home/engineering-stack.ts`
- Create: `tests/unit/engineering-stack.test.ts`

- [ ] **Step 1: Escrever os testes de conteúdo antes da implementação**

```ts
import { describe, expect, it } from "vitest";
import { engineeringToolGroups } from "../../src/components/home/engineering-stack";

describe("engineeringToolGroups", () => {
  it("mantém as camadas técnicas nos dois idiomas", () => {
    expect(engineeringToolGroups.pt.map((group) => group.slug)).toEqual([
      "data",
      "automation",
      "integration",
      "infrastructure",
      "cloud",
    ]);
    expect(engineeringToolGroups.en).toHaveLength(5);
  });

  it("marca Azure como competência em aprofundamento", () => {
    const azure = engineeringToolGroups.pt
      .flatMap((group) => group.tools)
      .find((tool) => tool.slug === "azure");

    expect(azure?.status).toBe("in-depth");
  });

  it("não deixa ferramentas sem nome, função ou marca visual", () => {
    for (const group of engineeringToolGroups.pt) {
      for (const tool of group.tools) {
        expect(tool.name.length).toBeGreaterThan(0);
        expect(tool.role.length).toBeGreaterThan(0);
        expect(tool.logo.length).toBeGreaterThan(0);
      }
    }
  });
});
```

- [ ] **Step 2: Rodar o teste para confirmar a falha inicial**

Run: `npm test -- tests/unit/engineering-stack.test.ts`

Expected: FAIL porque `src/components/home/engineering-stack.ts` ainda não existe.

- [ ] **Step 3: Implementar o catálogo mínimo**

Exportar estes tipos e dados em `engineering-stack.ts`:

```ts
export type ToolStatus = "confirmed" | "in-depth";
export type ToolGroupSlug =
  | "data"
  | "automation"
  | "integration"
  | "infrastructure"
  | "cloud";

export interface EngineeringTool {
  slug: string;
  name: string;
  role: string;
  logo: string;
  status: ToolStatus;
}

export interface EngineeringToolGroup {
  slug: ToolGroupSlug;
  title: string;
  tools: EngineeringTool[];
}

export const engineeringToolGroups: Record<"pt" | "en", EngineeringToolGroup[]> = {
  pt: [
    { slug: "data", title: "Dados e transformação", tools: [
      { slug: "python", name: "Python", role: "Parsing e regras", logo: "/images/tools/python.svg", status: "confirmed" },
      { slug: "sql", name: "SQL", role: "Consulta e modelagem", logo: "/images/tools/sql.svg", status: "confirmed" },
    ] },
    { slug: "automation", title: "Orquestração e automação", tools: [
      { slug: "kestra", name: "Kestra", role: "Orquestração", logo: "/images/tools/kestra.svg", status: "confirmed" },
      { slug: "playwright", name: "Playwright", role: "Automação web", logo: "/images/tools/playwright.svg", status: "confirmed" },
      { slug: "browserless", name: "Browserless", role: "Navegação remota", logo: "/images/tools/browserless.svg", status: "confirmed" },
    ] },
    { slug: "integration", title: "Integrações e mensageria", tools: [
      { slug: "evolution-api", name: "Evolution API", role: "Entrega de relatórios", logo: "/images/tools/evolution-api.svg", status: "confirmed" },
      { slug: "rest-webhooks", name: "REST e webhooks", role: "Integração de serviços", logo: "/images/tools/rest-webhooks.svg", status: "confirmed" },
    ] },
    { slug: "infrastructure", title: "Infraestrutura", tools: [
      { slug: "docker", name: "Docker", role: "Containers", logo: "/images/tools/docker.svg", status: "confirmed" },
      { slug: "linux", name: "Linux", role: "Operação de VM", logo: "/images/tools/linux.svg", status: "confirmed" },
      { slug: "coolify", name: "Coolify", role: "Deploy em VM", logo: "/images/tools/coolify.svg", status: "confirmed" },
      { slug: "git", name: "Git", role: "Versionamento", logo: "/images/tools/git.svg", status: "confirmed" },
    ] },
    { slug: "cloud", title: "Cloud", tools: [
      { slug: "azure", name: "Azure", role: "Em aprofundamento", logo: "/images/tools/azure.svg", status: "in-depth" },
    ] },
  ],
  en: [
    { slug: "data", title: "Data and transformation", tools: [
      { slug: "python", name: "Python", role: "Parsing and rules", logo: "/images/tools/python.svg", status: "confirmed" },
      { slug: "sql", name: "SQL", role: "Queries and modeling", logo: "/images/tools/sql.svg", status: "confirmed" },
    ] },
    { slug: "automation", title: "Orchestration and automation", tools: [
      { slug: "kestra", name: "Kestra", role: "Orchestration", logo: "/images/tools/kestra.svg", status: "confirmed" },
      { slug: "playwright", name: "Playwright", role: "Web automation", logo: "/images/tools/playwright.svg", status: "confirmed" },
      { slug: "browserless", name: "Browserless", role: "Remote browsing", logo: "/images/tools/browserless.svg", status: "confirmed" },
    ] },
    { slug: "integration", title: "Integrations and messaging", tools: [
      { slug: "evolution-api", name: "Evolution API", role: "Report delivery", logo: "/images/tools/evolution-api.svg", status: "confirmed" },
      { slug: "rest-webhooks", name: "REST and webhooks", role: "Service integration", logo: "/images/tools/rest-webhooks.svg", status: "confirmed" },
    ] },
    { slug: "infrastructure", title: "Infrastructure", tools: [
      { slug: "docker", name: "Docker", role: "Containers", logo: "/images/tools/docker.svg", status: "confirmed" },
      { slug: "linux", name: "Linux", role: "VM operations", logo: "/images/tools/linux.svg", status: "confirmed" },
      { slug: "coolify", name: "Coolify", role: "VM deployment", logo: "/images/tools/coolify.svg", status: "confirmed" },
      { slug: "git", name: "Git", role: "Version control", logo: "/images/tools/git.svg", status: "confirmed" },
    ] },
    { slug: "cloud", title: "Cloud", tools: [
      { slug: "azure", name: "Azure", role: "In progress", logo: "/images/tools/azure.svg", status: "in-depth" },
    ] },
  ],
};
```

- [ ] **Step 4: Rodar os testes de catálogo**

Run: `npm test -- tests/unit/engineering-stack.test.ts`

Expected: PASS com 3 testes.

- [ ] **Step 5: Commitar o catálogo**

```bash
git add src/components/home/engineering-stack.ts tests/unit/engineering-stack.test.ts
git commit -m "feat: add engineering stack catalog"
```

### Task 2: Adicionar marcas visuais locais

**Files:**
- Create: `public/images/tools/python.svg`
- Create: `public/images/tools/sql.svg`
- Create: `public/images/tools/kestra.svg`
- Create: `public/images/tools/playwright.svg`
- Create: `public/images/tools/browserless.svg`
- Create: `public/images/tools/evolution-api.svg`
- Create: `public/images/tools/rest-webhooks.svg`
- Create: `public/images/tools/docker.svg`
- Create: `public/images/tools/linux.svg`
- Create: `public/images/tools/coolify.svg`
- Create: `public/images/tools/git.svg`
- Create: `public/images/tools/azure.svg`

- [ ] **Step 1: Criar os SVGs locais em uma linguagem visual única**

Cada arquivo deve ser um SVG 48×48, monocromático, com `currentColor`, sem scripts, fontes externas ou chamadas remotas. Usar `title` interno com o nome da ferramenta e formas geométricas simples que permaneçam legíveis em 24px. As marcas devem ser tratadas como identificadores visuais compactos; o nome completo sempre ficará no HTML.

- [ ] **Step 2: Validar que os arquivos existem e não dependem de rede**

Run: `rg -n "(href|src)=\"https?://|<script|<foreignObject" public/images/tools`

Expected: nenhuma ocorrência.

- [ ] **Step 3: Commitar os assets**

```bash
git add public/images/tools
git commit -m "feat: add local engineering tool marks"
```

### Task 3: Construir o componente da faixa

**Files:**
- Create: `src/components/home/EngineeringStack.astro`

- [ ] **Step 1: Criar a estrutura sem animação**

O componente deve receber `groups` e `eyebrow`, `heading`, `intro` como propriedades. Renderizar uma seção `data-section="engineering-stack"`, um `h2`, uma breve introdução e uma lista por grupo. Cada ferramenta deve renderizar `img`, nome, função e, quando `status === "in-depth"`, o texto de estado.

- [ ] **Step 2: Adicionar a faixa duplicada para o loop**

Renderizar a mesma sequência duas vezes dentro de `.stack-track`; a segunda sequência terá `aria-hidden="true"`. O contêiner externo deve usar `overflow: hidden` e permitir foco nos itens da sequência acessível.

- [ ] **Step 3: Adicionar CSS responsivo e acessível**

Usar animação CSS lenta, `animation-play-state: paused` em `:hover` e `:focus-within`, e uma regra `@media (prefers-reduced-motion: reduce)` que remova a animação. O layout deve preservar o enquadramento padrão do site, evitar `width` fixo e não produzir overflow horizontal no documento.

- [ ] **Step 4: Commitar o componente**

```bash
git add src/components/home/EngineeringStack.astro
git commit -m "feat: add animated engineering stack section"
```

### Task 4: Integrar a seção bilíngue na home

**Files:**
- Modify: `src/pages/[lang]/index.astro:1-23`
- Modify: `src/pages/[lang]/index.astro:49-53`
- Modify: `src/pages/[lang]/index.astro:168-172`
- Modify: `src/pages/[lang]/index.astro:309-311`

- [ ] **Step 1: Trocar a importação e remover o estado vazio de métricas**

Importar `EngineeringStack`, importar `engineeringToolGroups` e remover `ImpactMetrics`, `Metric` e `aggregateMetrics` quando não forem mais utilizados.

- [ ] **Step 2: Substituir os textos de impacto por copy curta**

Português:

```ts
stack: {
  eyebrow: "Stack de engenharia",
  heading: "Ferramentas que sustentam a entrega.",
  intro: "Dados, automação e infraestrutura conectados ao problema real.",
}
```

Inglês:

```ts
stack: {
  eyebrow: "Engineering stack",
  heading: "Tools that sustain delivery.",
  intro: "Data, automation, and infrastructure connected to the real problem.",
}
```

- [ ] **Step 3: Renderizar a stack antes dos cases**

Substituir `<ImpactMetrics metrics={aggregateMetrics} {...copy.impact} />` por `<EngineeringStack groups={engineeringToolGroups[locale]} {...copy.stack} />`.

- [ ] **Step 4: Rodar checagem Astro e build**

Run: `npm run build`

Expected: `astro check` e `astro build` concluídos sem erros.

- [ ] **Step 5: Commitar a integração**

```bash
git add "src/pages/[lang]/index.astro"
git commit -m "feat: replace impact placeholder with engineering stack"
```

### Task 5: Atualizar testes da home e verificar a experiência

**Files:**
- Modify: `tests/e2e/home.spec.ts`

- [ ] **Step 1: Atualizar o teste de ordem das seções**

Trocar `impact-metrics` por `engineering-stack` no array esperado para PT e EN e trocar asserções do heading pela nova copy localizada.

- [ ] **Step 2: Cobrir ferramentas e o estado de Azure**

Adicionar asserções equivalentes a:

```ts
await expect(main.getByRole("heading", { name: "Ferramentas que sustentam a entrega." })).toBeVisible();
await expect(main.getByText("Docker", { exact: true })).toBeVisible();
await expect(main.getByText("Azure", { exact: true })).toBeVisible();
await expect(main.getByText("Em aprofundamento", { exact: true })).toBeVisible();
```

- [ ] **Step 3: Verificar redução de movimento e ausência de overflow**

Manter a asserção de `scrollWidth` já existente e adicionar um contexto Playwright com `reducedMotion: "reduce"` para confirmar que a faixa não depende da animação para exibir os itens.

- [ ] **Step 4: Executar a suíte relevante**

Run: `npm test -- tests/unit/engineering-stack.test.ts`

Expected: PASS.

Run: `npm run test:e2e -- tests/e2e/home.spec.ts`

Expected: PASS para PT, EN, responsividade e composição do Hero.

- [ ] **Step 5: Executar a verificação final do projeto**

Run: `npm run verify`

Expected: format, testes, conteúdo, build, E2E e links concluídos sem falhas.

- [ ] **Step 6: Commitar os testes**

```bash
git add tests/e2e/home.spec.ts
git commit -m "test: cover engineering stack home section"
```
