"use client";

import { useCurrentUser } from "@/hooks/use-current-user";
import { canAccessRole, type UserRole } from "@/lib/auth/roles";

/** Check role visibility against the current confirmed user. */
export function useCan(allowedRoles: readonly UserRole[]): boolean {
  const { data: user } = useCurrentUser();
  return user ? canAccessRole(user.role, allowedRoles) : false;
}
