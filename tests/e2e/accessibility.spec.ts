import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const pages = [
  "/pt/",
  "/en/",
  "/pt/projetos/",
  "/en/projects/",
  "/pt/projetos/venda-direta/",
  "/en/projects/direct-sales/",
  "/pt/sobre/",
  "/en/about/",
  "/404.html",
];

for (const path of pages) {
  test(`${path} has no serious accessibility violations`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter(
        ({ impact }) => impact === "serious" || impact === "critical",
      ),
    ).toEqual([]);
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).not.toHaveJSProperty(
      "tagName",
      "BODY",
    );
  });
}
