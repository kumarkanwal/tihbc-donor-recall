import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MaskedPhone } from "@/components/shared/masked-phone";

describe("MaskedPhone", () => {
  it("preserves an API-masked phone number", () => {
    render(<MaskedPhone value="+92300*****67" />);

    expect(screen.getByText("+92300*****67")).toBeVisible();
  });
});
