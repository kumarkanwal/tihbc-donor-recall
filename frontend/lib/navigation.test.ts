import { describe, expect, it } from "vitest";

import { getNavigationItem } from "@/lib/navigation";

describe("getNavigationItem", () => {
  it("uses the nearest parent route for nested pages", () => {
    expect(getNavigationItem("/batches/new").label).toBe("Donor Batches");
  });

  it("falls back to Dashboard for unknown routes", () => {
    expect(getNavigationItem("/unknown").label).toBe("Dashboard");
  });
});
