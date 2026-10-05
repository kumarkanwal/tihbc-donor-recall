"use client";

import { QueryProvider } from "@/components/shared/query-provider";
import { RealtimeProvider } from "@/components/shared/realtime-provider";
import { ThemeProvider } from "@/components/shared/theme-provider";
import { ToastViewport } from "@/components/shared/toast-viewport";

/** Compose browser-only application providers. */
export function AppProviders({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
    >
      <QueryProvider>
        <RealtimeProvider>{children}</RealtimeProvider>
        <ToastViewport />
      </QueryProvider>
    </ThemeProvider>
  );
}
