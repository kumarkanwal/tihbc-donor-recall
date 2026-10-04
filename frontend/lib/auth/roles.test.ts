import { describe, expect, it } from "vitest";

import { canAccessRole } from "@/lib/auth/roles";

describe("canAccessRole", () => {
  it("keeps admin-only controls hidden from coordinators", () => {
    expect(canAccessRole("admin", ["admin"])).toBe(true);
    expect(canAccessRole("coordinator", ["admin"])).toBe(false);
  });
});
