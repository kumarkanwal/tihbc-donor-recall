import { describe, expect, it } from "vitest";

import { parseWhatsAppFormat } from "./whatsapp-format";

describe("parseWhatsAppFormat", () => {
  it("returns plain, bold, and italic tokens without marker characters", () => {
    expect(parseWhatsAppFormat("Please *confirm* your _visit_.")).toEqual([
      { kind: "text", value: "Please " },
      { kind: "bold", value: "confirm" },
      { kind: "text", value: " your " },
      { kind: "italic", value: "visit" },
      { kind: "text", value: "." },
    ]);
  });
});
