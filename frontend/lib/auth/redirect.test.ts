import { describe, expect, it } from "vitest";

import { getSafeRedirectPath } from "@/lib/auth/redirect";

describe("getSafeRedirectPath", () => {
  it("keeps local application paths", () => {
    expect(getSafeRedirectPath("/campaigns/123")).toBe("/campaigns/123");
  });

  it.each([undefined, "https://example.com", "//example.com"])(
    "falls back to Dashboard for unsafe input",
    (input) => {
      expect(getSafeRedirectPath(input)).toBe("/");
    },
  );
});
