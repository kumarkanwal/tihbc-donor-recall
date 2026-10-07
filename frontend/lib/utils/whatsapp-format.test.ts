import { describe, expect, it } from "vitest";

import { parseWhatsAppFormat, splitBidiText } from "./whatsapp-format";

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

  it("separates Latin names and times for bidi isolation", () => {
    expect(
      splitBidiText("السلام Madiha Siddiqui، وقت 10:30 AM ہے").filter(
        ({ isolate }) => isolate,
      ),
    ).toEqual([
      { isolate: true, value: "Madiha Siddiqui" },
      { isolate: true, value: "10:30 AM" },
    ]);
  });
});
