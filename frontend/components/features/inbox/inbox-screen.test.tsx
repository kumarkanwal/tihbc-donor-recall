import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FollowUpDetail, FollowUpListItem } from "@/lib/api/contracts";

import { InboxScreen } from "./inbox-screen";

const mocks = vi.hoisted(() => ({
  useFollowUps: vi.fn(),
  useSummary: vi.fn(),
  useDetail: vi.fn(),
  openChat: vi.fn(),
}));

const mutation = { mutate: vi.fn(), isPending: false, error: null };

vi.mock("@/hooks/use-campaigns", () => ({
  useCampaignCatalog: () => ({ data: { items: [] } }),
}));
vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => ({ data: { id: "user-1" } }),
}));
vi.mock("@/hooks/use-follow-ups", () => ({
  useFollowUps: mocks.useFollowUps,
  useFollowUpSummary: mocks.useSummary,
  useFollowUp: mocks.useDetail,
  useExportFollowUps: () => mutation,
  useUpdateFollowUp: () => mutation,
  useAddFollowUpNote: () => mutation,
  useResolveFollowUp: () => mutation,
}));
vi.mock("@/lib/simulator/open-chat", () => ({
  openSimulatorChat: mocks.openChat,
}));

const item: FollowUpListItem = {
  id: "follow-up-1",
  enrollment_id: "enrollment-1",
  donor: { id: "donor-1", name: "Aisha Khan", phone: "+92300*****01" },
  campaign: { id: "campaign-1", name: "Recall campaign" },
  type: "needs_call",
  status: "open",
  priority: "high",
  latest_reply: { body: "Please call me", created_at: "2026-10-04T10:00:00Z" },
  assigned_to: null,
  created_at: "2026-10-04T10:00:00Z",
  updated_at: "2026-10-04T10:00:00Z",
};

const detail: FollowUpDetail = {
  ...item,
  donor: {
    ...item.donor,
    phone: "+923001234501",
    language: "en",
    segment: "regular",
    city: "Karachi",
    blood_group: "O+",
    last_donation_date: null,
  },
  enrollment: { id: "enrollment-1", status: "escalated" },
  latest_response: null,
  appointment: null,
  activities: [],
};

describe("InboxScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useFollowUps.mockReturnValue({
      data: { items: [item], total: 1, page: 1, page_size: 20 },
      isPending: false,
      error: null,
      refetch: vi.fn(),
    });
    mocks.useSummary.mockReturnValue({
      data: {
        total: 1,
        by_type: { needs_call: 1, reschedule: 0, declined: 0, confirmed: 0 },
        by_status: { open: 1, in_progress: 0, done: 0 },
      },
    });
    mocks.useDetail.mockReturnValue({
      data: detail,
      isPending: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("shows a retryable error when the inbox cannot load", () => {
    mocks.useFollowUps.mockReturnValue({
      data: undefined,
      isPending: false,
      error: new Error("network unavailable"),
      refetch: vi.fn(),
    });
    render(<InboxScreen />);
    expect(
      screen.getByText("The follow-up queue could not be loaded."),
    ).toBeVisible();
  });

  it("applies the selected follow-up type tab", async () => {
    const user = userEvent.setup();
    render(<InboxScreen />);
    await user.click(screen.getByRole("tab", { name: /Declined/ }));
    expect(mocks.useFollowUps).toHaveBeenLastCalledWith(
      expect.objectContaining({ type: "declined" }),
    );
  });

  it("opens the donor chat from the detail panel", async () => {
    const user = userEvent.setup();
    render(<InboxScreen />);
    await user.click(screen.getByRole("button", { name: /Aisha Khan/ }));
    await user.click(screen.getByRole("button", { name: "View chat" }));
    expect(mocks.openChat).toHaveBeenCalledWith("donor-1");
  });
});
