"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ComponentProps } from "react";

/** Apply the saved light, dark, or system preference through a root class. */
export function ThemeProvider({
  children,
  ...props
}: ComponentProps<typeof NextThemesProvider>): React.JSX.Element {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
