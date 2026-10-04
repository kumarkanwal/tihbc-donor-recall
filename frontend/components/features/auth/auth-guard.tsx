"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { SessionLoading } from "@/components/features/auth/session-loading";
import { ErrorState } from "@/components/shared/error-state";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { useSessionStore } from "@/lib/auth/session-store";

/** Prevent protected content from rendering before authentication resolves. */
export function AuthGuard({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  const hasMounted = useHasMounted();
  const pathname = usePathname();
  const router = useRouter();
  const token = useSessionStore((state) => state.token);
  const currentUser = useCurrentUser();

  useEffect(() => {
    if (hasMounted && !token) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [hasMounted, pathname, router, token]);

  if (!hasMounted || !token || currentUser.isPending) {
    return <SessionLoading />;
  }

  if (currentUser.isError) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <ErrorState
          description="We could not confirm your session. Check the API connection and retry."
          onRetry={() => void currentUser.refetch()}
        />
      </main>
    );
  }

  return <>{children}</>;
}
