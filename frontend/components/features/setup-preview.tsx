import { ArrowRight, FileUp } from "lucide-react";
import Image from "next/image";

import { StatusBadge } from "@/components/shared/status-badge";
import { ThemeSwitch } from "@/components/shared/theme-switch";
import { Button } from "@/components/ui/button";

const previewStatuses = [
  { status: "confirmed", label: "Confirmed" },
  { status: "pending", label: "Pending" },
  { status: "running", label: "Running" },
  { status: "declined", label: "Declined" },
] as const;

/** Temporary visual verification surface for the frontend foundation. */
export function SetupPreview(): React.JSX.Element {
  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-5xl justify-end">
        <ThemeSwitch />
      </div>

      <section className="rounded-card border-border bg-surface shadow-surface mx-auto mt-8 max-w-5xl overflow-hidden border dark:shadow-none">
        <div className="bg-accent h-1" />
        <div className="grid gap-10 p-6 sm:p-10 lg:grid-cols-[1.25fr_0.75fr] lg:p-14">
          <div className="flex flex-col justify-center">
            <div className="mb-8 flex items-center gap-4">
              <div className="rounded-card bg-white p-1.5">
                <Image
                  src="/images/IHHN-Logo-02-150x150.webp"
                  alt="Indus Hospital and Health Network"
                  width={64}
                  height={64}
                  priority
                />
              </div>
              <div>
                <p className="text-accent text-xs font-semibold tracking-wide uppercase">
                  TIHBC
                </p>
                <p className="text-muted-foreground text-sm">
                  Donor engagement platform
                </p>
              </div>
            </div>

            <h1 className="text-foreground text-3xl font-semibold tracking-tight sm:text-4xl">
              Donor Recall
            </h1>
            <p className="text-muted-foreground mt-4 max-w-xl text-base leading-7">
              A calm, focused workspace for reconnecting with blood donors and
              coordinating their next visit.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Button>
                <ArrowRight aria-hidden="true" strokeWidth={1.75} />
                Primary action
              </Button>
              <Button variant="secondary">
                <FileUp aria-hidden="true" strokeWidth={1.75} />
                Secondary action
              </Button>
            </div>
          </div>

          <div className="rounded-card border-border bg-surface-muted border p-6">
            <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
              Status system
            </p>
            <h2 className="text-foreground mt-2 text-lg font-semibold">
              Campaign activity
            </h2>
            <p className="text-muted-foreground mt-2 leading-6">
              Shared semantic colors keep every donor state easy to scan.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {previewStatuses.map(({ status, label }) => (
                <StatusBadge key={status} status={status} label={label} />
              ))}
            </div>
            <div className="border-border mt-8 border-t pt-6">
              <p className="text-muted-foreground text-sm">Urdu typography</p>
              <p lang="ur" dir="rtl" className="text-foreground mt-2 text-xl">
                خون کا عطیہ، زندگی کا تحفہ
              </p>
            </div>
          </div>
        </div>
      </section>

      <p className="text-muted-foreground mx-auto mt-5 max-w-5xl text-center text-xs">
        Temporary foundation preview for Task 3.1
      </p>
    </main>
  );
}
