import { expect, test } from "@playwright/test";

test("home exposes localized SEO metadata", async ({ page }) => {
  await page.goto("/pt/");

  await expect(page).toHaveTitle(
    "Engenheiro de Dados e Automação — Raffael Henrique",
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
  const jsonLdContent = await page
    .locator('script[type="application/ld+json"]')
    .textContent();
  if (jsonLdContent === null) throw new Error("JSON-LD script is missing");
  const jsonLd = JSON.parse(jsonLdContent) as {
    "@graph": Array<{ "@type": string; jobTitle?: string }>;
  };
  expect(
    jsonLd["@graph"].find((entry) => entry["@type"] === "Person"),
  ).toMatchObject({
    jobTitle: "Engenheiro de Dados e Automação",
  });

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
  expect(document).toContain('window.location.replace("/pt/")');
  expect(document).toContain('<a href="/pt/">Continuar em português</a>');
});
