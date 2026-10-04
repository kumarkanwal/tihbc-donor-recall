"use client";

import { Phone, X } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { useUiStore } from "@/lib/stores/ui-store";

/** Temporary simulator entry point and empty side panel. */
export function DonorPhonePanel(): React.JSX.Element {
  const isOpen = useUiStore((state) => state.isDonorPhoneOpen);
  const open = useUiStore((state) => state.openDonorPhone);
  const close = useUiStore((state) => state.closeDonorPhone);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        close();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [close, isOpen]);

  return (
    <>
      <Button
        type="button"
        className="shadow-surface fixed right-5 bottom-5 z-40"
        onClick={open}
        aria-haspopup="dialog"
      >
        <Phone aria-hidden="true" strokeWidth={1.75} />
        Donor Phone
      </Button>

      {isOpen ? (
        <div className="bg-foreground/20 fixed inset-0 z-50 flex justify-end">
          <button
            type="button"
            className="absolute inset-0 cursor-default"
            onClick={close}
            aria-label="Close donor phone"
          />
          <aside
            role="dialog"
            aria-modal="true"
            aria-labelledby="donor-phone-title"
            className="border-border bg-surface shadow-surface relative h-full w-full max-w-[400px] border-l"
          >
            <header className="border-border flex h-20 items-center justify-between border-b px-5">
              <div>
                <h2 id="donor-phone-title" className="text-lg font-semibold">
                  Donor Phone
                </h2>
                <p className="text-muted-foreground text-xs">
                  Simulator preview
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={close}
                aria-label="Close donor phone"
                autoFocus
              >
                <X aria-hidden="true" strokeWidth={1.75} />
              </Button>
            </header>
            <div className="flex h-[calc(100%-5rem)] items-center justify-center p-8 text-center">
              <div>
                <p className="font-medium">Simulator coming soon</p>
                <p className="text-muted-foreground mt-1 max-w-xs">
                  Donor conversations will appear here in Task 3.8.
                </p>
              </div>
            </div>
          </aside>
        </div>
      ) : null}
    </>
  );
}
