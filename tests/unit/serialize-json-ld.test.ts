import { describe, expect, it } from "vitest";
import {
  serializeJsonLd,
  type JsonLd,
} from "../../src/components/seo/serialize-json-ld";

describe("serializeJsonLd", () => {
  it("keeps hostile JSON-LD inside its script element and preserves its data", () => {
    const jsonLd: JsonLd = {
      "@context": "https://schema.org",
      description: "</script><script>alert(1)</script>&\u2028\u2029",
    };

    const serialized = serializeJsonLd(jsonLd);

    expect(serialized).not.toContain("</script>");
    expect(serialized).toContain("\\u003c/script\\u003e");
    expect(serialized).toContain("\\u003e");
    expect(serialized).toContain("\\u0026");
    expect(serialized).toContain("\\u2028");
    expect(serialized).toContain("\\u2029");
    expect(JSON.parse(serialized)).toEqual(jsonLd);
  });
});
