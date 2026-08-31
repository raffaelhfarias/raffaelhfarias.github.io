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
