import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UiState {
  isSidebarCollapsed: boolean;
  isDonorPhoneOpen: boolean;
  selectedDonorId: string | null;
  toggleSidebar: () => void;
  openDonorPhone: (donorId?: string) => void;
  closeDonorPhone: () => void;
  selectDonor: (donorId: string | null) => void;
}

/** Small persisted UI state shared by the application shell. */
export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      isDonorPhoneOpen: false,
      selectedDonorId: null,
      toggleSidebar: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      openDonorPhone: (donorId) =>
        set((state) => ({
          isDonorPhoneOpen: true,
          selectedDonorId: donorId ?? state.selectedDonorId,
        })),
      closeDonorPhone: () => set({ isDonorPhoneOpen: false }),
      selectDonor: (donorId) => set({ selectedDonorId: donorId }),
    }),
    {
      name: "donor-recall-ui",
      partialize: ({
        isDonorPhoneOpen,
        isSidebarCollapsed,
        selectedDonorId,
      }) => ({ isDonorPhoneOpen, isSidebarCollapsed, selectedDonorId }),
    },
  ),
);
