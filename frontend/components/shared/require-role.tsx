import type { ReactNode } from "react";

import { canAccessRole, type UserRole } from "@/lib/auth/roles";

interface RequireRoleProps {
  currentRole: UserRole;
  allowed: readonly UserRole[];
  children: ReactNode;
}

/** Hide controls that the current staff role cannot use. */
export function RequireRole({
  currentRole,
  allowed,
  children,
}: RequireRoleProps): ReactNode {
  return canAccessRole(currentRole, allowed) ? children : null;
}
