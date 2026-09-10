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
  await expect(
    main.getByRole("link", { name: "Solicitar currículo" }),
  ).toHaveAttribute("href", /mailto:.*subject=/);
  await expect(
    main.getByRole("complementary", {
      name: "Kestra / execução de workflow",
    }),
  ).toBeVisible();
  await expect(main.locator('[data-section="hero"]')).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Ferramentas que sustentam a entrega." }),
  ).toBeVisible();
  await expect(
    main
      .locator('[data-section="engineering-stack"]')
      .getByText("Docker", { exact: true })
      .first(),
  ).toBeVisible();
  await expect(main.getByAltText("Evolution API mark").first()).toBeVisible();
  await expect(
    main
      .locator('[data-section="engineering-stack"]')
      .getByText("Em aprofundamento", { exact: true })
      .first(),
  ).toBeVisible();
  await expect(
    main.getByRole("heading", { name: "Engenharia em produção" }),
  ).toBeVisible();
  expect(
    await main
      .locator("[data-section]")
      .evaluateAll((sections) =>
        sections.map((section) => section.getAttribute("data-section")),
      ),
  ).toEqual(["hero", "engineering-stack", "featured-cases"]);
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
  await expect(
    main.getByRole("heading", { name: "Tools that sustain delivery." }),
  ).toBeVisible();
  await expect(
    main
      .locator('[data-section="engineering-stack"]')
      .getByText("Docker", { exact: true })
      .first(),
  ).toBeVisible();
  await expect(
    main
      .locator('[data-section="engineering-stack"]')
      .getByText("In progress", { exact: true })
      .first(),
  ).toBeVisible();
  await expect(
    main.getByRole("link", { name: "Request tailored résumé" }),
  ).toHaveAttribute("href", /mailto:.*subject=/);
  await expect(
    main.getByRole("complementary", {
      name: "Kestra / workflow execution",
    }),
  ).toBeVisible();
  expect(
    await main
      .locator("[data-section]")
      .evaluateAll((sections) =>
        sections.map((section) => section.getAttribute("data-section")),
      ),
  ).toEqual(["hero", "engineering-stack", "featured-cases"]);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
});

test("home uses compact responsive typography and vertical rhythm", async ({
  page,
}) => {
  await page.goto("/pt/");

  const visualRhythm = await page.getByRole("main").evaluate((element) => {
    const hero = element.querySelector<HTMLElement>('[data-section="hero"]');
    const heading = hero?.querySelector<HTMLElement>("h1");
    const actions = hero?.querySelector<HTMLElement>(".hero-actions");
    const sectionPaddings = Array.from(
      element.querySelectorAll<HTMLElement>("[data-section]"),
      (section) => parseFloat(getComputedStyle(section).paddingTop),
    );

    if (!heading || !actions) throw new Error("Hero structure is missing");

    return {
      viewportWidth: window.innerWidth,
      headingSize: parseFloat(getComputedStyle(heading).fontSize),
      headingMarginBottom: parseFloat(getComputedStyle(heading).marginBottom),
      actionsMarginTop: parseFloat(getComputedStyle(actions).marginTop),
      maximumSectionPadding: Math.max(...sectionPaddings),
    };
  });
  const compact = visualRhythm.viewportWidth <= 768;

  expect(visualRhythm.headingSize).toBeLessThanOrEqual(compact ? 40 : 76);
  expect(visualRhythm.headingMarginBottom).toBeLessThanOrEqual(16);
  expect(visualRhythm.actionsMarginTop).toBeLessThanOrEqual(24);
  expect(visualRhythm.maximumSectionPadding).toBeLessThanOrEqual(
    compact ? 48 : 80,
  );
});

test("desktop hero heading is composed in three lines", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Desktop-only composition");
  for (const path of ["/pt/", "/en/"]) {
    await page.goto(path);

    const lineCount = await page
      .getByRole("heading", { level: 1 })
      .evaluate((heading) => {
        const range = document.createRange();
        range.selectNodeContents(heading);
        return new Set(
          Array.from(range.getClientRects(), (rect) => Math.round(rect.top)),
        ).size;
      });

    expect(lineCount).toBe(3);
  }
});

test("engineering stack remains visible with reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/pt/");

  const track = page.locator('[data-section="engineering-stack"] .stack-track');
  await expect(track).toBeVisible();
  await expect(track).toHaveCSS("animation-name", "none");
});
