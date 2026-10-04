import createClient, { type Middleware } from "openapi-fetch";

import { env } from "@/lib/env";
import type { paths } from "@/lib/api/schema";

import { getGeneratedClientBaseUrl } from "./base-url";
import { parseApiErrorPayload } from "./errors";
import { clearSessionAndRedirect, getAccessToken } from "./session";

async function readErrorPayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type");

  if (!contentType?.includes("application/json")) {
    return undefined;
  }

  try {
    return await response.clone().json();
  } catch (error: unknown) {
    if (error instanceof SyntaxError) {
      return undefined;
    }

    throw error;
  }
}

const apiMiddleware: Middleware = {
  onRequest({ request }) {
    const accessToken = getAccessToken();

    if (accessToken) {
      request.headers.set("Authorization", `Bearer ${accessToken}`);
    }

    return request;
  },
  async onResponse({ response }) {
    if (response.ok) {
      return response;
    }

    if (response.status === 401) {
      clearSessionAndRedirect();
    }

    const payload = await readErrorPayload(response);
    throw parseApiErrorPayload(response.status, payload);
  },
};

/** Generated-contract HTTP client with shared authentication and error behavior. */
export const apiClient = createClient<paths>({
  baseUrl: getGeneratedClientBaseUrl(env.NEXT_PUBLIC_API_URL),
});

apiClient.use(apiMiddleware);
