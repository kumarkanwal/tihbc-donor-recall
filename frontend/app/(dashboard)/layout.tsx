import { DashboardShell } from "@/components/features/app-shell/dashboard-shell";

/** Shared shell for authenticated application routes. */
export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  return <DashboardShell>{children}</DashboardShell>;
}
