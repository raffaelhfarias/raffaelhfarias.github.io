import { expect, test } from "@playwright/test";

test("home tells the recruiter story in the approved order", async ({
  page,
}) => {
  await page.goto("/pt/");

  const main = page.getByRole("main");
  await expect(
    main.getByRole("heading", {
      name: "Sistemas que transformam complexidade operacional em fluxo.",
    }),
  ).toBeVisible();
  await expect(
    main.getByRole("link", { name: "Explorar cases" }),
  ).toHaveAttribute("href", "/pt/projetos/");
  await expect(
    main.getByRole("link", { name: "Ver currículo" }),
  ).toHaveAttribute("href", "/cv/raffael-henrique-pt.pdf");
  await expect(
    main.getByRole("link", { name: "Currículo", exact: true }),
  ).toHaveAttribute("href", "/cv/raffael-henrique-pt.pdf");
  await expect(main.locator('[data-section="hero"]')).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Engenharia em produção" }),
  ).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Como trabalho" }),
  ).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Competências comprovadas" }),
  ).toBeVisible();
  await expect(main.getByRole("link", { name: "Ver evidência" })).toHaveCount(
    4,
  );
  await expect(
    main
      .getByRole("heading", { name: "Orquestração" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/pt/projetos/venda-direta/");
  await expect(
    main
      .getByRole("heading", { name: "Integração" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/pt/projetos/conciliacao-contabil/");
  await expect(
    main
      .getByRole("heading", { name: "Processamento de dados" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/pt/projetos/documentos-financeiros/");
  await expect(
    main
      .getByRole("heading", { name: "Confiabilidade operacional" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/pt/projetos/venda-direta/");
  expect(
    await main
      .locator("[data-section]")
      .evaluateAll((sections) =>
        sections.map((section) => section.getAttribute("data-section")),
      ),
  ).toEqual([
    "hero",
    "impact-metrics",
    "featured-cases",
    "work-process",
    "skills-evidence",
    "profile-summary",
    "contact",
  ]);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
});

test("English home is localized and preserves the approved section order", async ({
  page,
}) => {
  await page.goto("/en/");

  const main = page.getByRole("main");
  await expect(
    main.getByRole("heading", {
      name: "Systems that turn operational complexity into flow.",
    }),
  ).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Engineering in production" }),
  ).toBeVisible();
  await expect(main.getByRole("heading", { name: "How I work" })).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Proven capabilities" }),
  ).toBeVisible();
  await expect(main.getByRole("link", { name: "View résumé" })).toHaveAttribute(
    "href",
    "/cv/raffael-henrique-en.pdf",
  );
  await expect(
    main.getByRole("link", { name: "Résumé", exact: true }),
  ).toHaveAttribute("href", "/cv/raffael-henrique-en.pdf");
  await expect(main.getByRole("link", { name: "View evidence" })).toHaveCount(
    4,
  );
  await expect(
    main
      .getByRole("heading", { name: "Orchestration" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/en/projects/direct-sales/");
  await expect(
    main
      .getByRole("heading", { name: "Integration" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/en/projects/accounting-reconciliation/");
  await expect(
    main
      .getByRole("heading", { name: "Data processing" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/en/projects/financial-documents/");
  await expect(
    main
      .getByRole("heading", { name: "Operational reliability" })
      .locator("..")
      .getByRole("link"),
  ).toHaveAttribute("href", "/en/projects/direct-sales/");
  expect(
    await main
      .locator("[data-section]")
      .evaluateAll((sections) =>
        sections.map((section) => section.getAttribute("data-section")),
      ),
  ).toEqual([
    "hero",
    "impact-metrics",
    "featured-cases",
    "work-process",
    "skills-evidence",
    "profile-summary",
    "contact",
  ]);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
});
