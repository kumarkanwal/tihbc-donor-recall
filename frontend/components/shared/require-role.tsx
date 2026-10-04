import type { ReactNode } from "react";

import { useCan } from "@/hooks/use-can";
import type { UserRole } from "@/lib/auth/roles";

interface RequireRoleProps {
  allowed: readonly UserRole[];
  children: ReactNode;
}

/** Hide controls that the current staff role cannot use. */
export function RequireRole({
  allowed,
  children,
}: RequireRoleProps): ReactNode {
  return useCan(allowed) ? children : null;
}
