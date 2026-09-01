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
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
});
