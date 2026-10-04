import { describe, expect, it } from "vitest";

import {
  domainEnumValues,
  getStatusStyle,
} from "@/components/shared/status-badge";

describe("StatusBadge", () => {
  it("resolves every documented database enum value", () => {
    for (const value of domainEnumValues) {
      expect(getStatusStyle(value)).toBeTruthy();
    }
  });

  it("falls back to the muted treatment for unknown values", () => {
    expect(getStatusStyle("future_status")).toContain("text-muted-foreground");
  });
});
