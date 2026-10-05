import { apiClient } from "@/lib/api/client";

import { realtimeClient } from "@/lib/ws/client";
import type {
  ConversationFilters,
  SimulatorConversation,
  SimulatorDataSource,
  SimulatorEvent,
  SimulatorMessage,
  SimulatorReply,
  SimulatorMessagePage,
} from "./types";

function requireData<T>(data: T | undefined): T {
  if (data === undefined)
    throw new Error("The simulator API returned no data.");
  return data;
}

/** REST/WebSocket implementation matching the mock source boundary. */
export class ApiSimulatorSource implements SimulatorDataSource {
  async listConversations(
    filters: ConversationFilters = {},
  ): Promise<SimulatorConversation[]> {
    const items: SimulatorConversation[] = [];
    let page = 1;
    let total = 0;
    do {
      const { data } = await apiClient.GET("/api/v1/simulator/conversations", {
        params: { query: { ...filters, page, page_size: 100 } },
      });
      const result = requireData(data);
      items.push(...result.items);
      total = result.total;
      if (result.items.length === 0) break;
      page += 1;
    } while (items.length < total);
    return items;
  }

  async listMessages(donorId: string): Promise<SimulatorMessage[]> {
    return (await this.listMessagePage(donorId)).items;
  }

  async listMessagePage(
    donorId: string,
    before?: string,
  ): Promise<SimulatorMessagePage> {
    const { data } = await apiClient.GET(
      "/api/v1/simulator/conversations/{donor_id}/messages",
      { params: { path: { donor_id: donorId }, query: { before, limit: 50 } } },
    );
    return requireData(data);
  }

  async openConversation(donorId: string): Promise<void> {
    const { data } = await apiClient.POST(
      "/api/v1/simulator/conversations/{donor_id}/actions/open",
      { params: { path: { donor_id: donorId } } },
    );
    requireData(data);
  }

  async sendReply(
    donorId: string,
    reply: SimulatorReply,
  ): Promise<SimulatorMessage> {
    const { data } = await apiClient.POST(
      "/api/v1/simulator/conversations/{donor_id}/replies",
      { params: { path: { donor_id: donorId } }, body: reply },
    );
    return requireData(data);
  }

  subscribe(listener: (event: SimulatorEvent) => void): () => void {
    return realtimeClient.subscribe((event) => {
      if (
        event.type === "message.created" ||
        event.type === "message.status_updated" ||
        event.type === "simulator.typing"
      ) {
        listener(event);
      }
    });
  }
}

export const apiSimulatorSource = new ApiSimulatorSource();
