import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UiState {
  isSidebarCollapsed: boolean;
  isDonorPhoneOpen: boolean;
  toggleSidebar: () => void;
  openDonorPhone: () => void;
  closeDonorPhone: () => void;
}

/** Small persisted UI state shared by the application shell. */
export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      isDonorPhoneOpen: false,
      toggleSidebar: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      openDonorPhone: () => set({ isDonorPhoneOpen: true }),
      closeDonorPhone: () => set({ isDonorPhoneOpen: false }),
    }),
    {
      name: "donor-recall-ui",
      partialize: ({ isSidebarCollapsed }) => ({ isSidebarCollapsed }),
    },
  ),
);
