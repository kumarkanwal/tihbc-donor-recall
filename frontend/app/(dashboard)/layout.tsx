import { DashboardShell } from "@/components/features/app-shell/dashboard-shell";
import { AuthGuard } from "@/components/features/auth/auth-guard";

/** Shared shell for authenticated application routes. */
export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  return (
    <AuthGuard>
      <DashboardShell>{children}</DashboardShell>
    </AuthGuard>
  );
}
