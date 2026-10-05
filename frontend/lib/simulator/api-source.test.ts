import { afterEach, describe, expect, it, vi } from "vitest";
import { realtimeClient } from "@/lib/ws/client";
import { ApiSimulatorSource } from "./api-source";
import { createMockSeed } from "./mock-data";

const apiClient = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiClient }));
vi.mock("@/lib/ws/client", () => ({ realtimeClient: { subscribe: vi.fn() } }));
afterEach(() => vi.clearAllMocks());

describe("generated simulator API source", () => {
  it("reads all conversation pages and preserves nullable, masked donor fields", async () => {
    const [first, second] = createMockSeed().conversations;
    first.donor.phone = "+92300*****67";
    second.donor.campaign_id = null;
    second.donor.campaign_name = null;
    vi.mocked(apiClient.GET).mockResolvedValueOnce({
      data: { items: [first], total: 2, page: 1, page_size: 100 },
      response: new Response(),
    });
    vi.mocked(apiClient.GET).mockResolvedValueOnce({
      data: { items: [second], total: 2, page: 2, page_size: 100 },
      response: new Response(),
    });
    const rows = await new ApiSimulatorSource().listConversations({
      search: "Ahmed",
    });
    expect(rows).toEqual([first, second]);
    expect(rows[0].donor.phone).toBe("+92300*****67");
    expect(apiClient.GET).toHaveBeenLastCalledWith(
      "/api/v1/simulator/conversations",
      { params: { query: { search: "Ahmed", page: 2, page_size: 100 } } },
    );
  });
  it("passes the exclusive next_before cursor without reversing a chronological page", async () => {
    const message = {
      ...createMockSeed().conversations[0].last_message,
      buttons: null,
    };
    const page = { items: [message], next_before: "older-id", limit: 50 };
    vi.mocked(apiClient.GET).mockResolvedValue({
      data: page,
      response: new Response(),
    });
    expect(
      await new ApiSimulatorSource().listMessagePage(
        message.donor_id,
        "cursor-id",
      ),
    ).toEqual(page);
    expect(apiClient.GET).toHaveBeenCalledWith(
      "/api/v1/simulator/conversations/{donor_id}/messages",
      {
        params: {
          path: { donor_id: message.donor_id },
          query: { before: "cursor-id", limit: 50 },
        },
      },
    );
  });
  it("opens the thread and returns the saved inbound reply without fabricating a bot response", async () => {
    const inbound = {
      ...createMockSeed().conversations[0].last_message,
      direction: "inbound" as const,
      buttons: null,
    };
    vi.mocked(apiClient.POST).mockResolvedValueOnce({
      data: { read_count: 1 },
      response: new Response(),
    });
    vi.mocked(apiClient.POST).mockResolvedValueOnce({
      data: inbound,
      response: new Response(),
    });
    const source = new ApiSimulatorSource();
    await source.openConversation(inbound.donor_id);
    expect(
      await source.sendReply(inbound.donor_id, { type: "text", text: "Hello" }),
    ).toEqual(inbound);
    expect(apiClient.POST).toHaveBeenLastCalledWith(
      "/api/v1/simulator/conversations/{donor_id}/replies",
      {
        params: { path: { donor_id: inbound.donor_id } },
        body: { type: "text", text: "Hello" },
      },
    );
    expect(realtimeClient.subscribe).not.toHaveBeenCalled();
  });
  it("does not silently succeed when open returns no body", async () => {
    vi.mocked(apiClient.POST).mockResolvedValue({
      error: {},
      response: new Response(),
    });
    await expect(
      new ApiSimulatorSource().openConversation("donor-id"),
    ).rejects.toThrow("no data");
  });
});
