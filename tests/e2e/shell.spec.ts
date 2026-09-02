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

test("header omits the redundant tailored resume action", async ({ page }) => {
  for (const [path, label] of [
    ["/pt/", "Curr\u00edculo sob medida"],
    ["/en/", "Tailored r\u00e9sum\u00e9"],
  ] as const) {
    await page.goto(path);
    await expect(
      page.locator("header").getByRole("link", { name: label, exact: true }),
    ).toHaveCount(0);
  }
});

test("Portuguese-only articles omit the unavailable language switch", async ({
  page,
}) => {
  await page.goto("/pt/artigos/churn-prediction/");
  await expect(page.locator("header [data-language-switch]")).toHaveCount(0);
});
