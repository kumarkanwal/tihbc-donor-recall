"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { SessionLoading } from "@/components/features/auth/session-loading";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { apiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { clearSession, setSession } from "@/lib/api/session";
import { getSafeRedirectPath } from "@/lib/auth/redirect";
import { useSessionStore } from "@/lib/auth/session-store";

const loginSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

type LoginValues = z.infer<typeof loginSchema>;

interface LoginScreenProps {
  requestedPath?: string;
}

async function authenticate(values: LoginValues): Promise<void> {
  const { data: tokenResponse } = await apiClient.POST("/api/v1/auth/login", {
    body: values,
  });

  if (!tokenResponse) {
    throw new Error("The login response was empty.");
  }

  setSession(tokenResponse.access_token, tokenResponse.user);

  const { data: confirmedUser } = await apiClient.GET("/api/v1/auth/me");
  if (!confirmedUser) {
    clearSession();
    throw new Error("The current-user response was empty.");
  }

  setSession(tokenResponse.access_token, confirmedUser);
}

/** Validated staff login form and session bootstrap. */
export function LoginScreen({
  requestedPath,
}: LoginScreenProps): React.JSX.Element {
  const hasMounted = useHasMounted();
  const token = useSessionStore((state) => state.token);
  const router = useRouter();
  const redirectPath = getSafeRedirectPath(requestedPath);
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });
  const login = useMutation({
    mutationFn: authenticate,
    onSuccess: () => router.replace(redirectPath),
  });

  useEffect(() => {
    if (hasMounted && token) {
      router.replace("/");
    }
  }, [hasMounted, router, token]);

  if (!hasMounted || token) {
    return <SessionLoading />;
  }

  const errorMessage = login.isError
    ? login.error instanceof ApiError && login.error.status === 401
      ? "Invalid email or password"
      : "Unable to sign in. Please try again."
    : null;

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <section className="rounded-card border-border bg-surface shadow-surface w-full max-w-md border p-8">
        <div className="text-center">
          <span className="mx-auto block w-fit rounded-lg bg-white p-1.5">
            <Image
              src="/images/IHHN-Logo-02-150x150.webp"
              alt="Indus Hospital and Health Network"
              width={96}
              height={96}
              priority
            />
          </span>
          <h1 className="mt-5 text-2xl font-semibold">Donor Recall</h1>
          <p className="text-muted-foreground mt-1">
            Team Indus Health &amp; Blood Center
          </p>
        </div>

        <form
          className="mt-8 space-y-5"
          onSubmit={form.handleSubmit((values) => login.mutate(values))}
          noValidate
        >
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium">
              Email
            </label>
            <Input
              id="email"
              data-testid="login-email"
              type="email"
              autoComplete="email"
              aria-invalid={Boolean(form.formState.errors.email)}
              {...form.register("email")}
            />
            {form.formState.errors.email ? (
              <p className="text-danger mt-1 text-xs">
                {form.formState.errors.email.message}
              </p>
            ) : null}
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium"
            >
              Password
            </label>
            <Input
              id="password"
              data-testid="login-password"
              type="password"
              autoComplete="current-password"
              aria-invalid={Boolean(form.formState.errors.password)}
              {...form.register("password")}
            />
            {form.formState.errors.password ? (
              <p className="text-danger mt-1 text-xs">
                {form.formState.errors.password.message}
              </p>
            ) : null}
          </div>

          {errorMessage ? (
            <p className="text-danger text-sm" role="alert">
              {errorMessage}
            </p>
          ) : null}

          <Button
            type="submit"
            data-testid="login-submit"
            className="w-full"
            disabled={login.isPending}
          >
            {login.isPending ? "Signing in" : "Sign in"}
          </Button>
        </form>
      </section>
    </main>
  );
}
