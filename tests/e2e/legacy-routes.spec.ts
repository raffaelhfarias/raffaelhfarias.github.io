import { expect, test } from "@playwright/test";

import { legacyRoutes } from "../../src/data/legacy-routes";

for (const [legacy, destination] of Object.entries(legacyRoutes)) {
  test(`preserves /posts/${legacy}/`, async ({ request }) => {
    const response = await request.get(`/posts/${encodeURIComponent(legacy)}/`);
    const html = await response.text();
    expect(response.ok()).toBe(true);
    expect(html).toContain(`content="0;url=${destination}"`);
    expect(html).toContain(`href="${destination}"`);
    expect((await request.get(destination)).ok()).toBe(true);
  });
}
