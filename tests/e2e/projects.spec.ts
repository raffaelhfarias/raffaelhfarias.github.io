import { expect, test } from "@playwright/test";

test("Portuguese projects listing filters automation with ordinary links", async ({
  page,
}) => {
  await page.goto("/pt/projetos/");

  const filters = page.getByRole("navigation", { name: "Filtrar projetos" });
  await expect(filters.getByRole("link", { name: "Todos" })).toHaveAttribute(
    "aria-current",
    "page",
  );

  const automation = filters.locator('a[href="/pt/projetos/automacao/"]');
  await automation.click();

  await expect(page).toHaveURL("/pt/projetos/automacao/");
  await expect(automation).toHaveAttribute("aria-current", "page");
  await expect(page.locator("article").first()).toBeVisible();
  await expect(page.locator("article ul").first()).toHaveAttribute(
    "aria-label",
  );
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
});

for (const category of [
  {
    name: "Portuguese analytics",
    path: "/pt/projetos/analise-de-dados/",
    expectedSlug: "documentos-financeiros",
    unexpectedSlug: "venda-direta",
    alternateHreflang: "en",
    alternate: "https://raffaelhfarias.github.io/en/projects/analytics/",
  },
  {
    name: "English analytics",
    path: "/en/projects/analytics/",
    expectedSlug: "financial-documents",
    unexpectedSlug: "direct-sales",
    alternateHreflang: "pt-BR",
    alternate: "https://raffaelhfarias.github.io/pt/projetos/analise-de-dados/",
  },
]) {
  test(`${category.name} exposes only matching cards and localized SEO links`, async ({
    page,
  }) => {
    await page.goto(category.path);

    await expect(
      page.locator(`[data-project-slug="${category.expectedSlug}"]`),
    ).toHaveCount(1);
    await expect(
      page.locator(`[data-project-slug="${category.unexpectedSlug}"]`),
    ).toHaveCount(0);
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      `https://raffaelhfarias.github.io${category.path}`,
    );
    await expect(
      page.locator(`link[hreflang="${category.alternateHreflang}"]`),
    ).toHaveAttribute("href", category.alternate);
  });
}
