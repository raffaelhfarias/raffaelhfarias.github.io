export type JsonPrimitive = boolean | null | number | string;
export type JsonValue =
  JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type JsonLd = { [key: string]: JsonValue };

function assertJsonValue(
  value: unknown,
  ancestors: Set<object>,
): asserts value is JsonValue {
  if (
    value === null ||
    typeof value === "boolean" ||
    typeof value === "number" ||
    typeof value === "string"
  ) {
    return;
  }

  if (typeof value !== "object") {
    throw new TypeError(
      "JSON-LD values must be JSON primitives, arrays, or objects.",
    );
  }

  if (ancestors.has(value)) {
    throw new TypeError("JSON-LD cannot contain circular references.");
  }

  ancestors.add(value);
  for (const child of Array.isArray(value) ? value : Object.values(value)) {
    assertJsonValue(child, ancestors);
  }
  ancestors.delete(value);
}

export function serializeJsonLd(jsonLd: JsonLd): string {
  assertJsonValue(jsonLd, new Set());

  return JSON.stringify(jsonLd)
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}
