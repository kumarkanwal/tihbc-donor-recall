"use client";

import type { ReactNode } from "react";

import { DemoTimeProvider } from "@/components/shared/demo-time-provider";
import { DonorPhonePanel } from "@/components/features/app-shell/donor-phone-panel";
import { Sidebar } from "@/components/features/app-shell/sidebar";
import { TopBar } from "@/components/features/app-shell/top-bar";

/** Shared dashboard chrome around every application page. */
export function DashboardShell({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  return (
    <DemoTimeProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <TopBar />
          <main className="mx-auto w-full max-w-[1440px] p-4 pb-24 sm:p-6 sm:pb-24 lg:p-8 lg:pb-24">
            {children}
          </main>
        </div>
        <DonorPhonePanel />
      </div>
    </DemoTimeProvider>
  );
}
