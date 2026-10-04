import { z } from "zod";

const apiErrorPayloadSchema = z.object({
  error: z.object({
    code: z.string().min(1),
    message: z.string().min(1),
    details: z.record(z.string(), z.unknown()).default({}),
  }),
});

export type ApiErrorDetails = Record<string, unknown>;

/** Typed failure returned by the TIHBC API. */
export class ApiError extends Error {
  readonly code: string;
  readonly details: ApiErrorDetails;
  readonly status: number;

  constructor(
    status: number,
    code: string,
    message: string,
    details: ApiErrorDetails = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/** Convert the documented API error envelope into a typed application error. */
export function parseApiErrorPayload(
  status: number,
  payload: unknown,
): ApiError {
  const result = apiErrorPayloadSchema.safeParse(payload);

  if (!result.success) {
    return new ApiError(
      status,
      `HTTP_${status}`,
      `Request failed with status ${status}.`,
    );
  }

  return new ApiError(
    status,
    result.data.error.code,
    result.data.error.message,
    result.data.error.details,
  );
}
