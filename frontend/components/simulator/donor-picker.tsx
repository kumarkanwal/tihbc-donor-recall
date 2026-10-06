"use client";

import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { useCampaignCatalog } from "@/hooks/use-campaigns";
import { useSimulatorConversations } from "@/hooks/use-simulator";

import { ChatListItem } from "./chat-list-item";

/** Searchable, campaign-filtered donor conversation picker. */
export function DonorPicker({
  onSelect,
}: {
  onSelect: (donorId: string) => void;
}): React.JSX.Element {
  const [search, setSearch] = useState("");
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const runningCampaigns = useCampaignCatalog("running");
  const newestRunningCampaignId = useMemo(() => {
    const items = runningCampaigns.data?.items;
    if (!items?.length) return "";
    return [...items].sort((left, right) => {
      const leftTime = Date.parse(left.launched_at ?? left.start_at);
      const rightTime = Date.parse(right.launched_at ?? right.start_at);
      return rightTime - leftTime;
    })[0].id;
  }, [runningCampaigns.data?.items]);
  const effectiveCampaignId =
    campaignId ?? (runningCampaigns.isSuccess ? newestRunningCampaignId : "");
  const conversations = useSimulatorConversations({
    search: search || undefined,
    campaign_id: effectiveCampaignId || undefined,
  });
  const catalog = useSimulatorConversations({});
  const campaigns = new Map<string, string>();
  for (const { donor } of catalog.data ?? []) {
    if (donor.campaign_id && donor.campaign_name)
      campaigns.set(donor.campaign_id, donor.campaign_name);
  }

  return (
    <div className="bg-sim-incoming flex min-h-0 flex-1 flex-col">
      <div className="bg-sim-incoming space-y-2 p-2">
        <label className="bg-sim-wallpaper text-sim-secondary flex items-center gap-2 rounded-full px-3">
          <Search aria-hidden="true" className="size-3.5" />
          <span className="sr-only">Search donors</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search donors"
            className="text-sim-text placeholder:text-sim-secondary min-w-0 flex-1 bg-transparent py-2 text-xs outline-none"
          />
        </label>
        <label>
          <span className="sr-only">Filter by campaign</span>
          <select
            data-testid="simulator-campaign-filter"
            value={effectiveCampaignId}
            onChange={(event) => setCampaignId(event.target.value)}
            className="border-sim-secondary/30 bg-sim-incoming text-sim-text w-full rounded border px-2 py-1.5 text-xs"
          >
            <option value="">All campaigns</option>
            {[...campaigns].map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {conversations.isLoading ? (
          <div aria-label="Loading donors" className="space-y-2 p-3">
            {[0, 1, 2].map((item) => (
              <div
                key={item}
                className="bg-sim-wallpaper h-14 animate-pulse rounded"
              />
            ))}
          </div>
        ) : null}
        {conversations.isError ? (
          <div className="text-sim-text p-6 text-center text-xs">
            <p>Donor conversations could not be loaded.</p>
            <button
              type="button"
              className="text-sim-button mt-2 font-medium"
              onClick={() => void conversations.refetch()}
            >
              Try again
            </button>
          </div>
        ) : null}
        {conversations.data?.length === 0 ? (
          <p className="text-sim-secondary p-8 text-center text-xs">
            No donors match these filters.
          </p>
        ) : null}
        {conversations.data?.map((conversation) => (
          <ChatListItem
            key={conversation.donor.id}
            conversation={conversation}
            onSelect={() => onSelect(conversation.donor.id)}
          />
        ))}
      </div>
    </div>
  );
}
