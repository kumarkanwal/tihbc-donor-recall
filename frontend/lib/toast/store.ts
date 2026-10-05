import { create } from "zustand";

interface ToastMessage {
  id: number;
  title: string;
  description?: string;
}

interface ToastState {
  messages: ToastMessage[];
  show: (title: string, description?: string) => void;
  dismiss: (id: number) => void;
}

let nextToastId = 0;

/** Small application toast store usable from React and realtime event handlers. */
export const useToastStore = create<ToastState>((set) => ({
  messages: [],
  show: (title, description) => {
    nextToastId += 1;
    const message = { id: nextToastId, title, description };
    set((state) => ({ messages: [...state.messages, message] }));
    window.setTimeout(() => {
      set((state) => ({
        messages: state.messages.filter(({ id }) => id !== message.id),
      }));
    }, 5_000);
  },
  dismiss: (id) =>
    set((state) => ({
      messages: state.messages.filter((message) => message.id !== id),
    })),
}));

export function showToast(title: string, description?: string): void {
  useToastStore.getState().show(title, description);
}
