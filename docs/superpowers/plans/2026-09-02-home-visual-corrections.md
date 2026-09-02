# Home Visual Corrections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir o acesso pela raiz e compactar a home PT/EN, removendo os dois CTAs redundantes de currículo.

**Architecture:** Alterações localizadas na raiz, no Header, nos dados da home e nos estilos dos sete componentes da home. Nenhum token global ou página interna será alterado.

**Tech Stack:** Astro 7, CSS responsivo, Playwright.

---

### Task 1: Criar regressões focadas

**Files:**
- Modify: `tests/e2e/seo.spec.ts`
- Modify: `tests/e2e/shell.spec.ts`
- Modify: `tests/e2e/home.spec.ts`

- [ ] Adicionar ao teste da raiz a exigência de `window.location.replace("/pt/")`.
- [ ] Substituir o teste positivo do CTA do Header por asserções de ausência em PT e EN.
- [ ] Exigir ausência de “Currículo sob medida” / “Tailored résumé” na seção final.
- [ ] Medir CSS computado: Hero `font-size <= 76px`, padding das seções `<= 80px`, margem inferior do `h1 <= 16px` e margem dos botões `<= 24px`.
- [ ] Rodar `npx.cmd playwright test tests/e2e/seo.spec.ts tests/e2e/shell.spec.ts tests/e2e/home.spec.ts` e confirmar falhas causadas pelos quatro comportamentos antigos.

### Task 2: Implementar a correção localizada

**Files:**
- Modify: `src/pages/index.astro`
- Modify: `src/components/navigation/Header.astro`
- Modify: `src/pages/[lang]/index.astro`
- Modify: `src/components/home/Hero.astro`
- Modify: `src/components/home/ImpactMetrics.astro`
- Modify: `src/components/home/FeaturedCases.astro`
- Modify: `src/components/home/WorkProcess.astro`
- Modify: `src/components/home/SkillsEvidence.astro`
- Modify: `src/components/home/ProfileSummary.astro`
- Modify: `src/components/home/ContactCta.astro`

- [ ] Adicionar `<script is:inline>window.location.replace("/pt/");</script>` antes do fallback da raiz.
- [ ] Remover `resumeHref`, o link `.header-cta` e os estilos exclusivos desse link.
- [ ] Remover apenas o terceiro item das listas finais de contato PT/EN; preservar o CTA contextual do Hero.
- [ ] Aplicar ao Hero `padding-block: clamp(3rem, 6vw, 5rem)`, `font-size: clamp(2.5rem, 5vw, 4.75rem)`, margens `0.5rem/1rem`, ações `1.5rem` e grid gap máximo `2.5rem`.
- [ ] Limitar seções editoriais a `3rem` ou `clamp(3rem, 7vw, 5rem)` e reduzir margens de títulos de `2.5rem` para `1.5rem` onde aplicável.
- [ ] Rodar novamente os três arquivos E2E e confirmar GREEN em desktop e Pixel 7.

### Task 3: Verificar e publicar

**Files:**
- Verify only.

- [ ] Rodar `npm.cmd run build` e confirmar Astro check/build sem erros.
- [ ] Rodar Prettier nos arquivos alterados e `git diff --check`.
- [ ] Commitar a implementação, enviar `main` e acompanhar o workflow de Pages até o sucesso.
- [ ] Conferir `/` e `/pt/` publicados.
