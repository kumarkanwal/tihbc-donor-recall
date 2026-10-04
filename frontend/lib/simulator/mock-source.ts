import { createMockSeed } from "./mock-data";
import { resolveMockAutomaticReply } from "./mock-replies";
import type {
  ConversationFilters,
  SimulatorConversation,
  SimulatorDataSource,
  SimulatorDonor,
  SimulatorEvent,
  SimulatorMessage,
  SimulatorMessageStatus,
  SimulatorReply,
} from "./types";

const AUTO_REPLY_DELAY_MS = 1_500;
const DELIVERY_DELAY_MS = 50;
const READ_DELAY_MS = 250;

function now(): string {
  return new Date().toISOString();
}

/** In-memory simulator with realistic event timing for demos and tests. */
export class MockSimulatorSource implements SimulatorDataSource {
  private readonly conversations: ReturnType<
    typeof createMockSeed
  >["conversations"];
  private readonly messages: ReturnType<typeof createMockSeed>["messages"];
  private readonly listeners = new Set<(event: SimulatorEvent) => void>();
  private sequence = 0;

  constructor() {
    const seed = createMockSeed();
    this.conversations = seed.conversations;
    this.messages = seed.messages;
  }

  async listConversations(
    filters: ConversationFilters = {},
  ): Promise<SimulatorConversation[]> {
    const search = filters.search?.trim().toLocaleLowerCase() ?? "";
    return this.conversations.filter(({ donor }) => {
      const matchesCampaign =
        !filters.campaign_id || donor.campaign_id === filters.campaign_id;
      const matchesSearch =
        !search ||
        donor.name.toLocaleLowerCase().includes(search) ||
        donor.phone.includes(search);
      return matchesCampaign && matchesSearch;
    });
  }

  async listMessages(donorId: string): Promise<SimulatorMessage[]> {
    return [...(this.messages.get(donorId) ?? [])];
  }

  async openConversation(donorId: string): Promise<void> {
    const conversation = this.getConversation(donorId);
    conversation.unread_count = 0;
    if (!conversation.donor.read_receipts) return;
    for (const message of this.messages.get(donorId) ?? []) {
      if (message.direction === "outbound" && message.status === "delivered") {
        this.updateStatus(message, "read");
      }
    }
  }

  async sendReply(
    donorId: string,
    reply: SimulatorReply,
  ): Promise<SimulatorMessage> {
    const conversation = this.getConversation(donorId);
    if (!conversation.donor.sim_reachable) {
      throw new Error("This number is not available on the simulator service.");
    }
    const message = this.createDonorMessage(conversation.donor, reply);
    this.append(message);
    this.scheduleReply(conversation.donor, reply);
    return message;
  }

  subscribe(listener: (event: SimulatorEvent) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private getConversation(donorId: string): SimulatorConversation {
    const conversation = this.conversations.find(
      ({ donor }) => donor.id === donorId,
    );
    if (!conversation) throw new Error("Donor conversation was not found.");
    return conversation;
  }

  private createDonorMessage(
    donor: SimulatorDonor,
    reply: SimulatorReply,
  ): SimulatorMessage {
    const original =
      reply.type === "button"
        ? this.messages
            .get(donor.id)
            ?.find(({ id }) => id === reply.reply_to_message_id)
        : undefined;
    const label =
      reply.type === "text"
        ? reply.text
        : (original?.buttons.find(({ id }) => id === reply.button_id)?.label ??
          reply.button_id);
    return this.createMessage(donor.id, "inbound", label, {
      buttonId: reply.type === "button" ? reply.button_id : null,
      kind: reply.type === "button" ? "button_reply" : "text",
      replyTo: reply.type === "button" ? reply.reply_to_message_id : null,
      status: "sent",
    });
  }

  private scheduleReply(donor: SimulatorDonor, reply: SimulatorReply): void {
    const donorMessage = this.messages.get(donor.id)?.at(-1);
    if (!donorMessage) return;
    setTimeout(
      () => this.updateStatus(donorMessage, "delivered"),
      DELIVERY_DELAY_MS,
    );
    setTimeout(() => this.updateStatus(donorMessage, "read"), READ_DELAY_MS);
    this.emit({
      type: "simulator.typing",
      payload: { donor_id: donor.id, is_typing: true },
    });
    setTimeout(() => {
      this.emit({
        type: "simulator.typing",
        payload: { donor_id: donor.id, is_typing: false },
      });
      this.append(this.createAutomaticReply(donor, reply));
    }, AUTO_REPLY_DELAY_MS);
  }

  private createAutomaticReply(
    donor: SimulatorDonor,
    reply: SimulatorReply,
  ): SimulatorMessage {
    const response = resolveMockAutomaticReply(donor, reply);
    return this.createMessage(donor.id, "outbound", response.body, {
      buttons: response.buttons,
      kind: response.buttons.length > 0 ? "interactive" : "text",
      status: "delivered",
    });
  }

  private createMessage(
    donorId: string,
    direction: SimulatorMessage["direction"],
    body: string,
    options: {
      buttons?: { id: string; label: string }[];
      buttonId?: string | null;
      kind: SimulatorMessage["kind"];
      replyTo?: string | null;
      status: SimulatorMessageStatus;
    },
  ): SimulatorMessage {
    const timestamp = now();
    this.sequence += 1;
    return {
      id: `mock-message-${this.sequence}`,
      donor_id: donorId,
      direction,
      kind: options.kind,
      body,
      media_type: "none",
      media_url: null,
      buttons: options.buttons ?? [],
      button_id: options.buttonId ?? null,
      reply_to_message_id: options.replyTo ?? null,
      status: options.status,
      created_at: timestamp,
      sent_at: timestamp,
      delivered_at: options.status === "delivered" ? timestamp : null,
      read_at: options.status === "read" ? timestamp : null,
    };
  }

  private append(message: SimulatorMessage): void {
    const messages = this.messages.get(message.donor_id) ?? [];
    messages.push(message);
    this.messages.set(message.donor_id, messages);
    const conversation = this.getConversation(message.donor_id);
    conversation.last_message = message;
    this.emit({ type: "message.created", payload: message });
  }

  private updateStatus(
    message: SimulatorMessage,
    status: SimulatorMessageStatus,
  ): void {
    const timestamp = now();
    message.status = status;
    if (status === "delivered") message.delivered_at = timestamp;
    if (status === "read") message.read_at = timestamp;
    this.emit({
      type: "message.status_updated",
      payload: {
        id: message.id,
        donor_id: message.donor_id,
        status,
        delivered_at: message.delivered_at,
        read_at: message.read_at,
        failed_reason: null,
      },
    });
  }

  private emit(event: SimulatorEvent): void {
    for (const listener of this.listeners) listener(event);
  }
}

export const mockSimulatorSource = new MockSimulatorSource();
