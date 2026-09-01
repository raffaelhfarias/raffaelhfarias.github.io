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

  await filters.getByRole("link", { name: "AutomaÃ§Ã£o" }).click();

  await expect(page).toHaveURL("/pt/projetos/automacao/");
  await expect(
    filters.getByRole("link", { name: "AutomaÃ§Ã£o" }),
  ).toHaveAttribute("aria-current", "page");
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
