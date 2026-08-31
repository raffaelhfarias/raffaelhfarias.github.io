import { expect, test } from "@playwright/test";

test("home exposes localized SEO metadata", async ({ page }) => {
  await page.goto("/pt/");

  await expect(page).toHaveTitle(
    /Engenheiro de Dados e Automa..o.*Raffael Henrique/,
  );
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "https://raffaelhfarias.github.io/pt/",
  );
  await expect(page.locator('link[hreflang="en"]')).toHaveAttribute(
    "href",
    "https://raffaelhfarias.github.io/en/",
  );
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
    "content",
    /social-preview/,
  );
  await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(
    1,
  );

  await page.goto("/en/");
  await expect(page).toHaveTitle(
    /Data & Automation Engineer.*Raffael Henrique/,
  );
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "https://raffaelhfarias.github.io/en/",
  );
  await expect(page.locator('link[hreflang="pt-BR"]')).toHaveAttribute(
    "href",
    "https://raffaelhfarias.github.io/pt/",
  );
});

test("root provides a static-host compatible Portuguese redirect", async ({
  page,
}) => {
  const response = await page.request.get("/");
  const document = await response.text();

  expect(response.ok()).toBe(true);
  expect(document).toContain(
    '<meta http-equiv="refresh" content="0;url=/pt/">',
  );
  expect(document).toContain('<a href="/pt/">Continuar em portuguÃªs</a>');
});
