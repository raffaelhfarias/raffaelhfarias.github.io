import { expect, test } from "@playwright/test";

for (const path of [
  "/pt/",
  "/en/",
  "/pt/projetos/",
  "/en/projects/",
  "/pt/projetos/venda-direta/",
  "/en/projects/direct-sales/",
  "/pt/sobre/",
  "/en/about/",
  "/404.html",
]) {
  test(`${path} has no horizontal overflow at 390px`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(path);
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
  });
}
