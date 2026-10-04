import type { Metadata } from "next";
import { Inter, Noto_Nastaliq_Urdu } from "next/font/google";

import { AppProviders } from "@/components/shared/app-providers";
import { env } from "@/lib/env";
import "@/styles/globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const notoNastaliqUrdu = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  variable: "--font-noto-nastaliq-urdu",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Donor Recall",
    template: `%s | ${env.NEXT_PUBLIC_APP_NAME}`,
  },
  description: "TIHBC donor recall and rescheduling system",
};

/** Root document layout and browser providers. */
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): React.JSX.Element {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${notoNastaliqUrdu.variable}`}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
