export type SimulatorLanguage = "en" | "ur";
export type SimulatorMessageStatus =
  "queued" | "sent" | "delivered" | "read" | "failed";

export interface SimulatorButton {
  id: string;
  label: string;
}

/** Message shape defined by docs/api.md section 7. */
export interface SimulatorMessage {
  id: string;
  donor_id: string;
  direction: "outbound" | "inbound";
  kind: "template" | "text" | "interactive" | "button_reply";
  body: string;
  media_type: "none" | "image" | "video";
  media_url: string | null;
  buttons: SimulatorButton[];
  button_id: string | null;
  reply_to_message_id: string | null;
  status: SimulatorMessageStatus;
  created_at: string;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
}

export interface SimulatorDonor {
  id: string;
  name: string;
  phone: string;
  language: SimulatorLanguage;
  sim_reachable: boolean;
  read_receipts: boolean;
  campaign_id: string;
  campaign_name: string;
}

export interface SimulatorConversation {
  donor: SimulatorDonor;
  last_message: SimulatorMessage | null;
  unread_count: number;
}

export type SimulatorReply =
  | { type: "button"; button_id: string; reply_to_message_id: string }
  | { type: "text"; text: string };

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

export interface ConversationFilters {
  campaign_id?: string;
  search?: string;
}

/** Interchangeable mock/API boundary consumed by simulator hooks. */
export interface SimulatorDataSource {
  listConversations(
    filters?: ConversationFilters,
  ): Promise<SimulatorConversation[]>;
  listMessages(donorId: string): Promise<SimulatorMessage[]>;
  openConversation(donorId: string): Promise<void>;
  sendReply(donorId: string, reply: SimulatorReply): Promise<SimulatorMessage>;
  subscribe(listener: (event: SimulatorEvent) => void): () => void;
}
