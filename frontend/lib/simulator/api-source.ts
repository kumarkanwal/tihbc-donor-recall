import { apiClient } from "@/lib/api/client";

import { subscribeToSimulatorEvents } from "./websocket";
import type {
  ConversationFilters,
  SimulatorConversation,
  SimulatorDataSource,
  SimulatorEvent,
  SimulatorMessage,
  SimulatorReply,
} from "./types";

type ClientResult<T> = Promise<{ data?: T; error?: unknown }>;

interface SimulatorApiClient {
  GET(
    path: "/api/v1/simulator/conversations",
    options: { params: { query: ConversationFilters } },
  ): ClientResult<{ items: SimulatorConversation[] }>;
  GET(
    path: "/api/v1/simulator/conversations/{donor_id}/messages",
    options: { params: { path: { donor_id: string } } },
  ): ClientResult<{ items: SimulatorMessage[] }>;
  POST(
    path: "/api/v1/simulator/conversations/{donor_id}/actions/open",
    options: { params: { path: { donor_id: string } } },
  ): ClientResult<unknown>;
  POST(
    path: "/api/v1/simulator/conversations/{donor_id}/replies",
    options: {
      params: { path: { donor_id: string } };
      body: SimulatorReply;
    },
  ): ClientResult<SimulatorMessage>;
}

// Remove this narrow compatibility cast once Task 2.7 adds section-7 paths to OpenAPI.
const simulatorClient = apiClient as unknown as SimulatorApiClient;

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
    const { data } = await simulatorClient.GET(
      "/api/v1/simulator/conversations",
      { params: { query: filters } },
    );
    return requireData(data).items;
  }

  async listMessages(donorId: string): Promise<SimulatorMessage[]> {
    const { data } = await simulatorClient.GET(
      "/api/v1/simulator/conversations/{donor_id}/messages",
      { params: { path: { donor_id: donorId } } },
    );
    return requireData(data).items;
  }

  async openConversation(donorId: string): Promise<void> {
    await simulatorClient.POST(
      "/api/v1/simulator/conversations/{donor_id}/actions/open",
      { params: { path: { donor_id: donorId } } },
    );
  }

  async sendReply(
    donorId: string,
    reply: SimulatorReply,
  ): Promise<SimulatorMessage> {
    const { data } = await simulatorClient.POST(
      "/api/v1/simulator/conversations/{donor_id}/replies",
      { params: { path: { donor_id: donorId } }, body: reply },
    );
    return requireData(data);
  }

  subscribe(listener: (event: SimulatorEvent) => void): () => void {
    return subscribeToSimulatorEvents(listener);
  }
}

export const apiSimulatorSource = new ApiSimulatorSource();
