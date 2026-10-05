"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { useCan } from "@/hooks/use-can";
import {
  getCampaignLaunchProblems,
  useCreateCampaign,
  useLaunchCampaign,
  useUpdateCampaign,
  type CampaignCreate,
} from "@/hooks/use-campaigns";

import { CampaignForm } from "./campaign-form";

/** Administrator campaign creation and optional immediate launch flow. */
export function CampaignCreateScreen(): React.JSX.Element {
  const router = useRouter();
  const canCreate = useCan(["admin"]);
  const [draftId, setDraftId] = useState("");
  const createCampaign = useCreateCampaign();
  const updateCampaign = useUpdateCampaign(draftId);
  const launchCampaign = useLaunchCampaign();
  const error =
    launchCampaign.error ?? updateCampaign.error ?? createCampaign.error;
  const pending =
    createCampaign.isPending ||
    updateCampaign.isPending ||
    launchCampaign.isPending;

  if (!canCreate) {
    return (
      <ErrorState
        title="Administrator access required"
        description="Only administrators can create campaigns."
      />
    );
  }

  async function persist(input: CampaignCreate) {
    if (draftId) return updateCampaign.mutateAsync(input);
    const created = await createCampaign.mutateAsync(input);
    setDraftId(created.id);
    return created;
  }

  async function save(input: CampaignCreate): Promise<void> {
    try {
      const campaign = await persist(input);
      router.push(`/campaigns/${campaign.id}`);
    } catch {
      // Mutation errors render inline.
    }
  }

  async function launch(input: CampaignCreate): Promise<void> {
    try {
      const campaign = await persist(input);
      await launchCampaign.mutateAsync(campaign.id);
      router.push(`/campaigns/${campaign.id}`);
    } catch {
      // Aggregate launch problems render inline without losing the draft.
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="New campaign"
        description="Assign a donor batch to primary and secondary recall sequences."
        breadcrumb={<Link href="/campaigns">Campaigns</Link>}
      />
      <CampaignForm
        pending={pending}
        error={error}
        launchProblems={getCampaignLaunchProblems(launchCampaign.error)}
        allowLaunch
        onSave={(input) => void save(input)}
        onLaunch={(input) => void launch(input)}
      />
    </div>
  );
}
