import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LoginScreen } from "@/components/features/auth/login-screen";
import { ApiError } from "@/lib/api/errors";
import { clearSession } from "@/lib/api/session";

const apiMocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    GET: apiMocks.get,
    POST: apiMocks.post,
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

function TestProviders({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  return (
    <QueryClientProvider client={new QueryClient()}>
      {children}
    </QueryClientProvider>
  );
}

describe("LoginScreen", () => {
  afterEach(() => {
    clearSession();
    apiMocks.get.mockReset();
    apiMocks.post.mockReset();
  });

  it("shows the generic credential message for a 401", async () => {
    apiMocks.post.mockRejectedValue(
      new ApiError(401, "INVALID_CREDENTIALS", "Credentials rejected"),
    );
    const user = userEvent.setup();

    render(<LoginScreen />, { wrapper: TestProviders });
    await user.type(screen.getByLabelText("Email"), "admin@example.com");
    await user.type(screen.getByLabelText("Password"), "not-the-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid email or password",
    );
  });
});
