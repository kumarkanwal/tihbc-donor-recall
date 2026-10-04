import { useUiStore } from "@/lib/stores/ui-store";

/** Open the donor phone directly on one conversation. */
export function openSimulatorChat(donorId: string): void {
  useUiStore.getState().openDonorPhone(donorId);
}
