"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { BatchUploadWizard } from "@/components/features/batches/batch-upload-wizard";
import { SessionLoading } from "@/components/features/auth/session-loading";
import { useCurrentUser } from "@/hooks/use-current-user";

/** Keep coordinator sessions out of the admin-only batch upload flow. */
export function BatchUploadRoute(): React.JSX.Element {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (user && !isAdmin) {
      router.replace("/batches");
    }
  }, [isAdmin, router, user]);

  if (!isAdmin) {
    return <SessionLoading />;
  }

  return <BatchUploadWizard />;
}
