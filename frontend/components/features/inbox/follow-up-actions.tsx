"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/hooks/use-current-user";
import {
  useAddFollowUpNote,
  useResolveFollowUp,
  useUpdateFollowUp,
} from "@/hooks/use-follow-ups";
import type {
  FollowUpDetail,
  FollowUpOutcome,
} from "@/lib/api/pending-contracts";
import { openSimulatorChat } from "@/lib/simulator/open-chat";

/** Assignment, progress, note, resolution, and chat actions for one item. */
export function FollowUpActions({
  detail,
}: {
  detail: FollowUpDetail;
}): React.JSX.Element {
  const { data: user } = useCurrentUser();
  const update = useUpdateFollowUp(detail.id);
  const addNote = useAddFollowUpNote(detail.id);
  const resolve = useResolveFollowUp(detail.id);
  const [note, setNote] = useState("");
  const [resolveOpen, setResolveOpen] = useState(false);
  const [outcome, setOutcome] = useState<FollowUpOutcome>("attended");
  const [resolveNote, setResolveNote] = useState("");
  const pending = update.isPending || addNote.isPending || resolve.isPending;
  const error = update.error ?? addNote.error ?? resolve.error;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {!detail.assigned_to && user ? (
          <Button
            type="button"
            variant="secondary"
            disabled={pending}
            onClick={() => update.mutate({ assigned_to_id: user.id })}
          >
            Assign to me
          </Button>
        ) : null}
        {detail.status === "open" ? (
          <Button
            type="button"
            variant="secondary"
            disabled={pending}
            onClick={() => update.mutate({ status: "in_progress" })}
          >
            Start
          </Button>
        ) : null}
        {detail.status !== "done" ? (
          <Button
            type="button"
            disabled={pending}
            onClick={() => setResolveOpen((value) => !value)}
          >
            Resolve
          </Button>
        ) : null}
        <Button
          type="button"
          variant="secondary"
          onClick={() => openSimulatorChat(detail.donor.id)}
        >
          View chat
        </Button>
      </div>
      {resolveOpen ? (
        <div className="bg-surface-muted rounded-card space-y-3 p-4">
          <label className="block text-sm font-medium">
            Outcome
            <select
              value={outcome}
              onChange={(event) =>
                setOutcome(event.target.value as FollowUpOutcome)
              }
              className="border-border bg-surface rounded-control mt-1 h-10 w-full border px-3"
            >
              <option value="attended">Attended</option>
              <option value="rebooked">Rebooked</option>
              <option value="not_reachable">Not reachable</option>
            </select>
          </label>
          <label className="block text-sm font-medium">
            Resolution note (optional)
            <textarea
              value={resolveNote}
              onChange={(event) => setResolveNote(event.target.value)}
              className="border-border bg-surface rounded-control mt-1 min-h-20 w-full border p-3"
            />
          </label>
          <Button
            type="button"
            disabled={pending}
            onClick={() =>
              resolve.mutate({
                outcome,
                note: resolveNote.trim() || undefined,
              })
            }
          >
            Confirm resolution
          </Button>
        </div>
      ) : null}
      <form
        className="space-y-2"
        onSubmit={(event) => {
          event.preventDefault();
          const value = note.trim();
          if (!value) return;
          addNote.mutate(value, { onSuccess: () => setNote("") });
        }}
      >
        <label htmlFor="follow-up-note" className="text-sm font-medium">
          Add note
        </label>
        <textarea
          id="follow-up-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          className="border-border bg-surface rounded-control min-h-20 w-full border p-3"
          placeholder="Add context for the next coordinator"
        />
        <Button
          type="submit"
          variant="secondary"
          disabled={pending || !note.trim()}
        >
          Save note
        </Button>
      </form>
      {error ? (
        <p role="alert" className="text-danger text-sm">
          {error.message}
        </p>
      ) : null}
    </div>
  );
}
