"use client";

import { Phone, X } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { useSimulatorConversations } from "@/hooks/use-simulator";
import { useUiStore } from "@/lib/stores/ui-store";
import { cn } from "@/lib/utils/class-names";

import { ConversationScreen } from "./conversation-screen";
import { DonorPicker } from "./donor-picker";
import { SimulatorPhoneFrame } from "./phone-frame";
import { ViewingAsBanner } from "./viewing-as-banner";

/** Persistent donor-phone launcher and slide-in simulator panel. */
export function SimulatorPanel(): React.JSX.Element {
  const isOpen = useUiStore((state) => state.isDonorPhoneOpen);
  const selectedDonorId = useUiStore((state) => state.selectedDonorId);
  const open = useUiStore((state) => state.openDonorPhone);
  const close = useUiStore((state) => state.closeDonorPhone);
  const selectDonor = useUiStore((state) => state.selectDonor);
  const conversations = useSimulatorConversations({});
  const selectedConversation = conversations.data?.find(
    ({ donor }) => donor.id === selectedDonorId,
  );

  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") close();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [close, isOpen]);

  return (
    <>
      <Button
        type="button"
        data-testid="donor-phone-launcher"
        className="shadow-surface fixed right-5 bottom-5 z-40"
        onClick={() => open()}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
      >
        <Phone aria-hidden="true" strokeWidth={1.75} />
        Donor Phone
      </Button>
      <aside
        data-testid="donor-phone-panel"
        role="dialog"
        aria-modal="false"
        aria-label="Donor phone simulator"
        aria-hidden={!isOpen}
        inert={!isOpen}
        className={cn(
          "border-border bg-surface shadow-surface fixed inset-y-0 right-0 z-50 w-full max-w-[400px] border-l p-3 transition-transform duration-300",
          isOpen ? "translate-x-0" : "pointer-events-none translate-x-full",
        )}
      >
        <button
          type="button"
          data-testid="donor-phone-close"
          onClick={close}
          aria-label="Close donor phone"
          className="border-border bg-surface text-foreground absolute top-3 -left-11 flex size-10 items-center justify-center rounded-l-md border border-r-0 shadow-sm"
        >
          <X aria-hidden="true" className="size-4" />
        </button>
        {selectedConversation ? (
          <ViewingAsBanner donor={selectedConversation.donor} />
        ) : null}
        <SimulatorPhoneFrame
          header={
            selectedConversation ? (
              false
            ) : (
              <header className="bg-sim-header text-sim-header-text flex h-14 items-center px-4 text-sm font-semibold">
                Select donor
              </header>
            )
          }
          className={cn(
            "flex h-[calc(100vh-1.5rem)] max-h-[760px] flex-col",
            selectedConversation && "h-[calc(100vh-4.5rem)]",
          )}
        >
          {selectedConversation ? (
            <ConversationScreen
              conversation={selectedConversation}
              onBack={() => selectDonor(null)}
            />
          ) : (
            <DonorPicker onSelect={(donorId) => selectDonor(donorId)} />
          )}
        </SimulatorPhoneFrame>
      </aside>
    </>
  );
}
