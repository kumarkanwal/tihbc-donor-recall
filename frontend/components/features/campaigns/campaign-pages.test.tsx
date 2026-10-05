import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CampaignDetailActions } from "./campaign-detail-actions";
import { CampaignForm } from "./campaign-form";
import { CampaignListScreen } from "./campaign-list-screen";
import { CampaignSummary } from "./campaign-summary";
import { EnrollmentTable } from "./enrollment-table";
import { LaunchProblems } from "./launch-problems";
import type { CampaignDetail, Enrollment } from "@/hooks/use-campaigns";
import type { ContentSeriesDetail } from "@/hooks/use-content-series";
import type { DonorBatchDetail } from "@/hooks/use-donor-batches";

const mocks = vi.hoisted(() => ({
  canManage: vi.fn(),
  launch: vi.fn(),
  openChat: vi.fn(),
  pause: vi.fn(),
  push: vi.fn(),
  resume: vi.fn(),
  useCampaignCatalog: vi.fn(),
}));

const idleMutation = {
  mutate: vi.fn(),
  mutateAsync: vi.fn(),
  isPending: false,
  error: null,
};

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: mocks.push }) }));
vi.mock("@/hooks/use-can", () => ({ useCan: mocks.canManage }));
vi.mock("@/lib/simulator/open-chat", () => ({
  openSimulatorChat: mocks.openChat,
}));
vi.mock("@/hooks/use-campaigns", () => ({
  getCampaignErrorMessage: (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback,
  getCampaignLaunchProblems: () => [],
  useCampaignCatalog: mocks.useCampaignCatalog,
  useLaunchCampaign: () => ({ ...idleMutation, mutate: mocks.launch }),
  usePauseCampaign: () => ({ ...idleMutation, mutate: mocks.pause }),
  useResumeCampaign: () => ({ ...idleMutation, mutate: mocks.resume }),
}));
vi.mock("@/hooks/use-donor-batches", () => ({
  useDonorBatches: () => ({ data: { items: [], total: 0 }, error: null }),
  useDonorBatch: () => ({ data: undefined }),
}));
vi.mock("@/hooks/use-content-series", () => ({
  useContentSeries: () => ({ data: { items: [], total: 0 }, error: null }),
  useContentSeriesDetail: () => ({ data: undefined }),
}));

const campaign: CampaignDetail = {
  id: "campaign-id",
  name: "Task 2.3 Manual Test",
  batch: { id: "batch-id", name: "October Donors" },
  primary_series: { id: "primary-id", name: "Regular Recall" },
  secondary_series: { id: "secondary-id", name: "Final Follow-up" },
  status: "running",
  start_at: "2026-10-04T10:00:00Z",
  enrollment_count: 10,
  responded_count: 4,
  response_rate: 40,
  enrollment_counts: { pending: 6, confirmed: 4 },
  created_by: { id: "user-id", full_name: "Admin User" },
  created_at: "2026-10-04T09:00:00Z",
  updated_at: "2026-10-04T10:00:00Z",
  launched_at: "2026-10-04T10:00:00Z",
  completed_at: null,
};

const batch: DonorBatchDetail = {
  id: "batch-id",
  name: "Bilingual donors",
  original_filename: "donors.csv",
  total_rows: 10,
  valid_rows: 10,
  invalid_rows: 0,
  campaign_count: 0,
  segment_breakdown: [{ segment: "regular", count: 10 }],
  language_breakdown: [
    { language: "en", count: 5 },
    { language: "ur", count: 5 },
  ],
  uploaded_by: { id: "user-id", full_name: "Admin User" },
  created_at: "2026-10-04T09:00:00Z",
};

function series(
  kind: "primary" | "secondary",
  languages: ("en" | "ur")[],
): ContentSeriesDetail {
  return {
    id: `${kind}-id`,
    name: `${kind} series`,
    description: null,
    kind,
    status: "active",
    languages,
    response_window_hours: 48,
    tags: [],
    step_count: 1,
    steps: [
      {
        id: `${kind}-step`,
        step_order: 1,
        delay_days: 0,
        category: "utility",
        media_type: "none",
        media_url: null,
        contents: [],
        buttons: [],
      },
    ],
    created_by: { id: "user-id", full_name: "Admin User" },
    created_at: "2026-10-04T09:00:00Z",
    updated_at: "2026-10-04T09:00:00Z",
  };
}

const enrollment: Enrollment = {
  id: "enrollment-id",
  campaign_id: campaign.id,
  donor: {
    id: "donor-id",
    full_name: "Aisha Khan",
    phone_e164: "+92300*****67",
    segment: "regular",
    language: "en",
    city: "Karachi",
    blood_group: "O+",
    last_donation_date: "2026-06-01",
  },
  status: "in_primary",
  current_series_kind: "primary",
  current_step_order: 1,
  next_action_at: null,
  responded_at: null,
  decline_reason: null,
  created_at: "2026-10-04T10:00:00Z",
  updated_at: "2026-10-04T10:00:00Z",
};

describe("Campaign pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.canManage.mockReturnValue(true);
    mocks.useCampaignCatalog.mockReturnValue({
      data: { items: [campaign], total: 1, page: 1, page_size: 100 },
      isPending: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders every backend launch problem", () => {
    render(
      <LaunchProblems
        problems={[
          { field: "primary_series_id", reason: "Series must be active" },
          {
            field: "batch_id",
            reason: "Batch is already used by another campaign",
          },
        ]}
      />,
    );
    expect(screen.getByText(/Primary series:/)).toBeVisible();
    expect(screen.getByText(/Series must be active/)).toBeVisible();
    expect(screen.getByText(/already used/)).toBeVisible();
  });

  it("warns when a selected series does not cover a donor language", () => {
    render(
      <CampaignSummary
        batch={batch}
        primary={series("primary", ["en"])}
        secondary={series("secondary", ["en", "ur"])}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Primary series is missing Urdu",
    );
  });

  it("filters the campaign query when a status tab is selected", async () => {
    const user = userEvent.setup();
    render(<CampaignListScreen />);
    await user.click(screen.getByRole("tab", { name: "Running" }));
    expect(mocks.useCampaignCatalog).toHaveBeenLastCalledWith("running");
  });

  it("shows pause and resume only for their matching statuses", () => {
    const { rerender } = render(
      <CampaignDetailActions campaign={campaign} canManage />,
    );
    expect(screen.getByRole("button", { name: "Pause" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Resume" })).toBeNull();
    rerender(
      <CampaignDetailActions
        campaign={{ ...campaign, status: "paused" }}
        canManage
      />,
    );
    expect(screen.getByRole("button", { name: "Resume" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Pause" })).toBeNull();
  });

  it("keeps coordinator campaign settings read-only", () => {
    render(
      <CampaignForm
        campaign={{ ...campaign, status: "draft" }}
        readOnly
        onSave={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Campaign name")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Save changes" })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Launch campaign" }),
    ).toBeNull();
  });

  it("opens the donor phone from View chat", async () => {
    const user = userEvent.setup();
    render(
      <EnrollmentTable
        data={{ items: [enrollment], total: 1, page: 1, page_size: 20 }}
        isPending={false}
        error={null}
        onSearchChange={vi.fn()}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        onDetails={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: "View chat" }));
    expect(mocks.openChat).toHaveBeenCalledWith("donor-id");
  });
});
