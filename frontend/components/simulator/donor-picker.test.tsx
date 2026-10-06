import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { createMockSeed } from "@/lib/simulator/mock-data";

import { DonorPicker } from "./donor-picker";

const mocks = vi.hoisted(() => ({
  useConversations: vi.fn(),
}));

vi.mock("@/hooks/use-simulator", () => ({
  useSimulatorConversations: (filters: unknown) =>
    mocks.useConversations(filters),
}));

vi.mock("@/hooks/use-campaigns", () => ({
  useCampaignCatalog: () => ({
    data: {
      items: [
        {
          id: "campaign-regular",
          start_at: "2026-10-01T05:00:00Z",
          launched_at: "2026-10-01T05:00:00Z",
        },
        {
          id: "campaign-lapsed",
          start_at: "2026-10-05T05:00:00Z",
          launched_at: "2026-10-05T05:00:00Z",
        },
      ],
    },
    isSuccess: true,
  }),
}));

describe("DonorPicker", () => {
  it("defaults to the newest running campaign and labels rows by campaign", async () => {
    const conversations = createMockSeed().conversations;
    mocks.useConversations.mockReturnValue({
      data: conversations,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<DonorPicker onSelect={vi.fn()} />);

    await waitFor(() =>
      expect(screen.getByLabelText("Filter by campaign")).toHaveValue(
        "campaign-lapsed",
      ),
    );
    expect(mocks.useConversations).toHaveBeenCalledWith(
      expect.objectContaining({ campaign_id: "campaign-lapsed" }),
    );
    expect(
      screen.getAllByText(/October Regular Recall/).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Lapsed Donor Win-back/).length).toBeGreaterThan(
      0,
    );
  });
});
