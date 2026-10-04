import { describe, expect, it } from "vitest";

import { getGeneratedClientBaseUrl } from "@/lib/api/base-url";

describe("getGeneratedClientBaseUrl", () => {
  it("does not duplicate the generated API version path", () => {
    expect(getGeneratedClientBaseUrl("http://localhost:8000/api/v1")).toBe(
      "http://localhost:8000",
    );
  });

  it("preserves a deployment path before the API version", () => {
    expect(getGeneratedClientBaseUrl("https://example.com/demo/api/v1")).toBe(
      "https://example.com/demo",
    );
  });
});
