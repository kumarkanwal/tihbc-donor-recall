import { describe, expect, it } from "vitest";

import { ApiError, parseApiErrorPayload } from "./errors";

describe("parseApiErrorPayload", () => {
  it("creates a typed error from the documented error envelope", () => {
    const error = parseApiErrorPayload(422, {
      error: {
        code: "VALIDATION_ERROR",
        message: "The upload contains invalid rows.",
        details: { invalid_rows: 2 },
      },
    });

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      code: "VALIDATION_ERROR",
      message: "The upload contains invalid rows.",
      details: { invalid_rows: 2 },
    });
  });

  it("returns a safe generic error for an invalid payload", () => {
    const error = parseApiErrorPayload(502, { message: "Proxy failure" });

    expect(error).toMatchObject({
      status: 502,
      code: "HTTP_502",
      message: "Request failed with status 502.",
      details: {},
    });
  });
});
