"use client";

import { Pause, Play } from "lucide-react";

import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";
import {
  getCampaignErrorMessage,
  getCampaignLaunchProblems,
  useLaunchCampaign,
  usePauseCampaign,
  useResumeCampaign,
  type CampaignDetail,
} from "@/hooks/use-campaigns";

import { LaunchProblems } from "./launch-problems";

/** Role- and state-aware campaign lifecycle controls. */
export function CampaignDetailActions({
  campaign,
  canManage,
}: {
  campaign: CampaignDetail;
  canManage: boolean;
}): React.JSX.Element | null {
  const launch = useLaunchCampaign();
  const pause = usePauseCampaign();
  const resume = useResumeCampaign();
  if (!canManage) return null;
  const error = launch.error ?? pause.error ?? resume.error;
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {campaign.status === "draft" ? (
          <ConfirmDialog
            trigger={
              <Button type="button">
                <Play aria-hidden="true" />
                Launch
              </Button>
            }
            title="Launch campaign?"
            description="Every valid donor in this batch will be enrolled. A live campaign using the same batch will block launch."
            confirmLabel="Launch campaign"
            pending={launch.isPending}
            onConfirm={() => launch.mutate(campaign.id)}
          />
        ) : null}
        {campaign.status === "running" ? (
          <Button
            type="button"
            variant="secondary"
            disabled={pause.isPending}
            onClick={() => pause.mutate(campaign.id)}
          >
            <Pause aria-hidden="true" />
            Pause
          </Button>
        ) : null}
        {campaign.status === "paused" ? (
          <Button
            type="button"
            disabled={resume.isPending}
            onClick={() => resume.mutate(campaign.id)}
          >
            <Play aria-hidden="true" />
            Resume
          </Button>
        ) : null}
      </div>
      <LaunchProblems problems={getCampaignLaunchProblems(launch.error)} />
      {error && getCampaignLaunchProblems(error).length === 0 ? (
        <p role="alert" className="text-danger max-w-md text-sm">
          {getCampaignErrorMessage(
            error,
            "The campaign status could not be changed.",
          )}
        </p>
      ) : null}
    </div>
  );
}
