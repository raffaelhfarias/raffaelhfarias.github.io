import { expect, test } from "@playwright/test";

test("renders the Portuguese recruiter-first shell", async ({ page }) => {
  await page.goto("/pt/");

  await expect(page.getByRole("banner")).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Principal" }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
});

test("language switch preserves the equivalent public route", async ({
  page,
}) => {
  await page.goto("/pt/projetos/venda-direta/");
  await expect(page.locator("header [data-language-switch]")).toHaveAttribute(
    "href",
    "/en/projects/direct-sales/",
  );

  await page.goto("/en/projects/direct-sales/");
  await expect(page.locator("header [data-language-switch]")).toHaveAttribute(
    "href",
    "/pt/projetos/venda-direta/",
  );
});

test("header offers a tailored resume request without a generic PDF", async ({
  page,
}) => {
  await page.goto("/pt/");
  await expect(
    page.locator("header").getByRole("link", {
      name: "Curr\u00edculo sob medida",
      exact: true,
    }),
  ).toHaveAttribute("href", /mailto:.*subject=/);
  await expect(page.locator('header a[href^="/cv/"]')).toHaveCount(0);
});

test("Portuguese-only articles omit the unavailable language switch", async ({
  page,
}) => {
  await page.goto("/pt/artigos/churn-prediction/");
  await expect(page.locator("header [data-language-switch]")).toHaveCount(0);
});
