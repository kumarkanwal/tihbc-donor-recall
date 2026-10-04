"use client";

import type { ReactNode } from "react";

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
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <TopBar />
        <main className="mx-auto w-full max-w-[1440px] p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
      <DonorPhonePanel />
    </div>
  );
}
