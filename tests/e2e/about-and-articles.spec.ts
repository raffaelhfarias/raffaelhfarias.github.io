import { expect, test } from "@playwright/test";

for (const profile of [
  {
    path: "/pt/sobre/",
    heading: "Engenharia de dados aplicada a operações reais",
    portraitAlt: "Retrato de Raffael Henrique",
    resume: "Solicitar currículo para a vaga",
  },
  {
    path: "/en/about/",
    heading: "Data engineering applied to real operations",
    portraitAlt: "Portrait of Raffael Henrique",
    resume: "Request a role-specific résumé",
  },
]) {
  test(`${profile.path} renders the localized professional profile`, async ({
    page,
  }) => {
    await page.goto(profile.path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      profile.heading,
    );
    await expect(page.getByAltText(profile.portraitAlt)).toBeVisible();
    await expect(
      page.getByRole("link", { name: profile.resume }),
    ).toHaveAttribute("href", /mailto:.*subject=/);
    await expect(page.getByRole("link", { name: "GitHub" })).toHaveAttribute(
      "href",
      "https://github.com/raffaelhfarias",
    );
    await expect(page.getByRole("link", { name: "LinkedIn" })).toHaveAttribute(
      "href",
      "https://www.linkedin.com/in/raffael-henrique/",
    );
    await expect(page.locator('a[href^="mailto:"]')).not.toHaveCount(0);
    await expect(page.locator('a[href^="/cv/"]')).toHaveCount(0);
  });
}

test("Portuguese archive exposes a migrated analytical article", async ({
  page,
}) => {
  await page.goto("/pt/artigos/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Artigos");
  await page.getByRole("link", { name: "Analisando a Taxa de Churn" }).click();
  await expect(page).toHaveURL("/pt/artigos/churn-prediction/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Analisando a Taxa de Churn",
  );
  await expect(
    page.locator('link[rel="alternate"][hreflang="en"]'),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: /notebook no GitHub/i }),
  ).toBeVisible();
});

test("English archive does not silently fall back to Portuguese", async ({
  page,
}) => {
  await page.goto("/en/articles/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Articles");
  await expect(page.locator("article")).toHaveCount(0);
  await expect(
    page.getByText("Portuguese-only articles are not duplicated here."),
  ).toBeVisible();
});
