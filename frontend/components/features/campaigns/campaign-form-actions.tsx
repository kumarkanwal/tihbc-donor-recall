import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";

interface CampaignFormActionsProps {
  isExisting: boolean;
  allowLaunch: boolean;
  pending: boolean;
  onLaunch: () => void;
}

/** Draft save and confirmed launch actions for an editable campaign form. */
export function CampaignFormActions({
  isExisting,
  allowLaunch,
  pending,
  onLaunch,
}: CampaignFormActionsProps): React.JSX.Element {
  return (
    <div className="mt-6 flex flex-wrap justify-end gap-2">
      <Button type="submit" variant="secondary" disabled={pending}>
        {pending ? "Saving" : isExisting ? "Save changes" : "Save as draft"}
      </Button>
      {allowLaunch ? (
        <ConfirmDialog
          trigger={
            <Button
              type="button"
              data-testid="campaign-launch-trigger"
              disabled={pending}
            >
              Launch campaign
            </Button>
          }
          title="Launch campaign?"
          description="This will enroll every valid donor in the selected batch and begin or schedule messaging."
          confirmLabel="Launch campaign"
          pending={pending}
          onConfirm={onLaunch}
        />
      ) : null}
    </div>
  );
}
