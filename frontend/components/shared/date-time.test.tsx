import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DateTime, formatDateTime } from "@/components/shared/date-time";

describe("DateTime", () => {
  it("formats UTC values in Asia/Karachi", () => {
    expect(formatDateTime("2026-10-03T05:30:00Z")).toBe(
      "03 Oct 2026, 10:30 AM",
    );
  });

  it("can render a relative label with an absolute tooltip", () => {
    render(
      <DateTime
        value="2026-10-03T06:30:00Z"
        relative
        now={new Date("2026-10-03T05:30:00Z")}
      />,
    );

    expect(screen.getByText("in 1 hour")).toHaveAttribute(
      "title",
      "03 Oct 2026, 11:30 AM",
    );
  });
});
