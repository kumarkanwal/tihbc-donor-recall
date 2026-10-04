"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { useSimulatorConversations } from "@/hooks/use-simulator";
import { MOCK_CAMPAIGNS } from "@/lib/simulator/mock-data";

import { ChatListItem } from "./chat-list-item";

/** Searchable, campaign-filtered donor conversation picker. */
export function DonorPicker({
  onSelect,
}: {
  onSelect: (donorId: string) => void;
}): React.JSX.Element {
  const [search, setSearch] = useState("");
  const [campaignId, setCampaignId] = useState("");
  const conversations = useSimulatorConversations({
    search: search || undefined,
    campaign_id: campaignId || undefined,
  });

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
            value={campaignId}
            onChange={(event) => setCampaignId(event.target.value)}
            className="border-sim-secondary/30 bg-sim-incoming text-sim-text w-full rounded border px-2 py-1.5 text-xs"
          >
            <option value="">All campaigns</option>
            {MOCK_CAMPAIGNS.map((campaign) => (
              <option key={campaign.id} value={campaign.id}>
                {campaign.name}
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
