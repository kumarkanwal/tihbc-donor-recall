import type { components, operations } from "@/lib/api/schema";

export type SimulatorLanguage = components["schemas"]["LanguageCode"];
export type SimulatorMessageStatus = components["schemas"]["MessageStatus"];
export type SimulatorButton = components["schemas"]["MessageButton"];
export type SimulatorMessage = components["schemas"]["SimulatorMessage"];
export type SimulatorDonor = components["schemas"]["SimulatorDonor"];
export type SimulatorConversation =
  components["schemas"]["SimulatorConversation"];
export type SimulatorMessagePage = components["schemas"]["MessagePage"];
export type SimulatorReply =
  components["schemas"]["ButtonReply"] | components["schemas"]["TextReply"];

export type SimulatorEvent =
  | { type: "message.created"; payload: SimulatorMessage }
  | {
      type: "message.status_updated";
      payload: {
        id: string;
        donor_id: string;
        status: SimulatorMessageStatus;
        delivered_at: string | null;
        read_at: string | null;
        failed_reason: string | null;
      };
    }
  | {
      type: "simulator.typing";
      payload: { donor_id: string; is_typing: boolean };
    };

export type ConversationFilters = NonNullable<
  operations["conversations_api_v1_simulator_conversations_get"]["parameters"]["query"]
>;

/** Interchangeable mock/API boundary consumed by simulator hooks. */
export interface SimulatorDataSource {
  listConversations(
    filters?: ConversationFilters,
  ): Promise<SimulatorConversation[]>;
  listMessages(donorId: string): Promise<SimulatorMessage[]>;
  listMessagePage(
    donorId: string,
    before?: string,
  ): Promise<SimulatorMessagePage>;
  openConversation(donorId: string): Promise<void>;
  sendReply(donorId: string, reply: SimulatorReply): Promise<SimulatorMessage>;
  subscribe(listener: (event: SimulatorEvent) => void): () => void;
}
