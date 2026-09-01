import { expect, test } from "@playwright/test";

test("featured case proves responsibility, architecture, reliability, and impact", async ({
  page,
}) => {
  await page.goto("/pt/projetos/venda-direta/");

  await expect(
    page.getByRole("heading", { level: 1, name: "Venda direta" }),
  ).toBeVisible();

  for (const heading of [
    "Minha responsabilidade",
    "Arquitetura",
    "Decisões técnicas",
    "Confiabilidade",
    "Resultados",
    "Aprendizados",
  ]) {
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
  }

  await expect(page.locator("[data-metric]")).not.toHaveCount(0);
  await expect(page.locator("figure").getByRole("img")).toHaveAttribute(
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
