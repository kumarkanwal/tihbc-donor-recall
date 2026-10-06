import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { createMockSeed } from "@/lib/simulator/mock-data";
import type { SimulatorMessage } from "@/lib/simulator";
import { DemoTimeContext } from "@/lib/demo-time";

import { ChatListItem } from "./chat-list-item";
import { MessageList } from "./message-list";
import { SimulatorMessageBubble } from "./message-bubble";
import { MessageTicks } from "./message-ticks";
import { SimulatorStatusBar } from "./status-bar";

const baseMessage: SimulatorMessage = {
  id: "message-one",
  donor_id: "donor-aisha",
  direction: "outbound",
  kind: "interactive",
  body: "Please *confirm* your visit.",
  media_type: "none",
  media_url: null,
  buttons: [{ id: "btn_confirm", label: "Confirm" }],
  button_id: null,
  reply_to_message_id: null,
  status: "delivered",
  created_at: "2026-10-04T09:30:00Z",
  sent_at: "2026-10-04T09:30:01Z",
  delivered_at: "2026-10-04T09:30:02Z",
  read_at: null,
};

describe("simulator presentation", () => {
  it("renders sent, delivered, and read tick states", () => {
    const { rerender } = render(<MessageTicks status="sent" />);
    expect(screen.getByLabelText("Sent")).toBeInTheDocument();
    rerender(<MessageTicks status="delivered" />);
    expect(screen.getByLabelText("Delivered")).toBeInTheDocument();
    rerender(<MessageTicks status="read" />);
    expect(screen.getByLabelText("Read").firstElementChild).toHaveClass(
      "text-sim-read",
    );
  });

  it("disables quick replies after a donor reply references the message", () => {
    Element.prototype.scrollTo = vi.fn();
    const reply: SimulatorMessage = {
      ...baseMessage,
      id: "message-reply",
      direction: "inbound",
      kind: "button_reply",
      body: "Confirm",
      buttons: [],
      button_id: "btn_confirm",
      reply_to_message_id: baseMessage.id,
      status: "read",
    };
    render(
      <MessageList
        messages={[baseMessage, reply]}
        language="en"
        isTyping={false}
        onButtonReply={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
  });

  it("uses automatic direction and the Urdu font for Urdu content", () => {
    render(
      <SimulatorMessageBubble
        body="آپ دوبارہ خون عطیہ کر سکتے ہیں۔"
        language="ur"
      />,
    );
    const content = screen
      .getByText("آپ دوبارہ خون عطیہ کر سکتے ہیں۔")
      .closest('[dir="auto"]');
    expect(content).toHaveAttribute("dir", "auto");
    expect(content).toHaveClass("font-urdu");
  });

  it("greys unreachable donors and explains why", () => {
    const seed = createMockSeed();
    const unreachable = seed.conversations.find(
      ({ donor }) => !donor.sim_reachable,
    );
    expect(unreachable).toBeDefined();
    render(<ChatListItem conversation={unreachable!} onSelect={vi.fn()} />);
    expect(screen.getByText("Number not on WhatsApp")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bilal Raza/ })).toHaveClass(
      "opacity-60",
    );
  });

  it("shows the Karachi demo-clock time in the phone status bar", () => {
    render(
      <DemoTimeContext.Provider value={new Date("2026-10-06T14:51:00Z")}>
        <SimulatorStatusBar />
      </DemoTimeContext.Provider>,
    );
    expect(screen.getByText("19:51")).toBeVisible();
  });
});
