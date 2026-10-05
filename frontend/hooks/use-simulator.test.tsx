import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  useSimulatorConversations,
  useSimulatorMessages,
} from "./use-simulator";
import { createMockSeed } from "@/lib/simulator/mock-data";
import { useUiStore } from "@/lib/stores/ui-store";

const source = vi.hoisted(() => ({
  listMessagePage: vi.fn(),
  listConversations: vi.fn(),
}));
const environment = vi.hoisted(() => ({
  NEXT_PUBLIC_SIMULATOR_SOURCE: "api",
  NEXT_PUBLIC_REALTIME: false,
}));
vi.mock("@/lib/simulator", () => ({ simulatorSource: source }));
vi.mock("@/lib/env", () => ({ env: environment }));

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  useUiStore.getState().closeDonorPhone();
  environment.NEXT_PUBLIC_REALTIME = false;
});

function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  useUiStore.getState().openDonorPhone("donor-aisha");
  return { client, wrapper };
}

describe("simulator message queries", () => {
  it.each([false, true])(
    "polls conversations at 10s only without realtime (%s)",
    async (realtime) => {
      vi.useFakeTimers();
      environment.NEXT_PUBLIC_REALTIME = realtime;
      const { wrapper, client } = setup();
      source.listConversations.mockResolvedValue([]);
      const { unmount } = renderHook(() => useSimulatorConversations({}), {
        wrapper,
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1);
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(9998);
      });
      expect(source.listConversations).toHaveBeenCalledTimes(1);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2);
      });
      expect(source.listConversations).toHaveBeenCalledTimes(realtime ? 1 : 2);
      unmount();
      client.clear();
    },
  );
  it("loads older pages using next_before and presents older messages first", async () => {
    const { wrapper, client } = setup();
    const message = createMockSeed().conversations[0].last_message;
    source.listMessagePage.mockResolvedValueOnce({
      items: [message],
      limit: 50,
      next_before: "older-cursor",
    });
    source.listMessagePage.mockResolvedValueOnce({
      items: [{ ...message, id: "older" }],
      limit: 50,
      next_before: null,
    });
    const { result, unmount } = renderHook(
      () => useSimulatorMessages("donor-aisha"),
      { wrapper },
    );
    await waitFor(() => expect(result.current.hasNextPage).toBe(true));
    await act(async () => {
      await result.current.fetchNextPage();
    });
    await waitFor(() =>
      expect(result.current.data?.map(({ id }) => id)).toEqual([
        "older",
        message.id,
      ]),
    );
    expect(source.listMessagePage).toHaveBeenLastCalledWith(
      "donor-aisha",
      "older-cursor",
    );
    expect(result.current.hasNextPage).toBe(false);
    unmount();
    client.clear();
  });

  it.each([false, true])(
    "polls only with realtime off (realtime=%s)",
    async (realtime) => {
      vi.useFakeTimers();
      environment.NEXT_PUBLIC_REALTIME = realtime;
      const { wrapper, client } = setup();
      source.listMessagePage.mockResolvedValue({
        items: [],
        limit: 50,
        next_before: null,
      });
      const { unmount } = renderHook(
        () => useSimulatorMessages("donor-aisha"),
        { wrapper },
      );
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1);
      });
      expect(source.listMessagePage).toHaveBeenCalledTimes(1);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3000);
      });
      expect(source.listMessagePage).toHaveBeenCalledTimes(realtime ? 1 : 2);
      act(() => useUiStore.getState().closeDonorPhone());
      await act(async () => {
        await vi.advanceTimersByTimeAsync(6000);
      });
      expect(source.listMessagePage).toHaveBeenCalledTimes(realtime ? 1 : 2);
      unmount();
      client.clear();
    },
  );
});
