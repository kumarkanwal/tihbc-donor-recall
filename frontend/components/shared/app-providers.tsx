"use client";

import { QueryProvider } from "@/components/shared/query-provider";
import { ThemeProvider } from "@/components/shared/theme-provider";

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
      <QueryProvider>{children}</QueryProvider>
    </ThemeProvider>
  );
}
