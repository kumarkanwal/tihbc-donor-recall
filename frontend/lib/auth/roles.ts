export type UserRole = "admin" | "coordinator";

/** Return whether a role is included in an allowed role set. */
export function canAccessRole(
  currentRole: UserRole,
  allowedRoles: readonly UserRole[],
): boolean {
  return allowedRoles.includes(currentRole);
}
