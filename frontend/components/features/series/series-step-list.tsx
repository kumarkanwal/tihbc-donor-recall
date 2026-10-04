"use client";

import { ArrowDown, ArrowUp, GripVertical, Plus } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { SeriesStep } from "@/hooks/use-content-series";
import { cn } from "@/lib/utils/class-names";

interface SeriesStepListProps {
  steps: SeriesStep[];
  selectedStepId: string | null;
  readOnly: boolean;
  pending: boolean;
  onSelect: (step: SeriesStep) => void;
  onAdd: () => void;
  onReorder: (stepIds: string[]) => void;
}

/** Ordered cards with pointer drag and explicit keyboard-accessible movement. */
export function SeriesStepList({
  steps,
  selectedStepId,
  readOnly,
  pending,
  onSelect,
  onAdd,
  onReorder,
}: SeriesStepListProps): React.JSX.Element {
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const reorder = (fromId: string, toId: string) => {
    const ids = steps.map((step) => step.id);
    const from = ids.indexOf(fromId);
    const to = ids.indexOf(toId);
    if (from < 0 || to < 0 || from === to) return;
    const [moved] = ids.splice(from, 1);
    ids.splice(to, 0, moved);
    onReorder(ids);
  };
  const move = (index: number, change: -1 | 1) => {
    const target = steps[index + change];
    if (target) reorder(steps[index].id, target.id);
  };

  return (
    <section className="border-border bg-surface rounded-card border p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Message steps</h2>
          <p className="text-muted-foreground text-sm">
            Messages send in this order.
          </p>
        </div>
        {!readOnly ? (
          <Button type="button" size="small" onClick={onAdd}>
            <Plus aria-hidden="true" />
            Add step
          </Button>
        ) : null}
      </div>
      {steps.length ? (
        <ol className="mt-4 space-y-2">
          {steps.map((step, index) => (
            <li
              key={step.id}
              draggable={!readOnly && !pending}
              onDragStart={(event) => {
                setDraggedId(step.id);
                event.dataTransfer.effectAllowed = "move";
              }}
              onDragOver={(event) => {
                if (!readOnly) event.preventDefault();
              }}
              onDrop={(event) => {
                event.preventDefault();
                if (draggedId) reorder(draggedId, step.id);
                setDraggedId(null);
              }}
              className={cn(
                "border-border rounded-card flex items-center gap-2 border p-2",
                selectedStepId === step.id && "border-primary bg-primary-soft",
              )}
            >
              <GripVertical
                aria-hidden="true"
                className="text-muted-foreground size-4 shrink-0"
              />
              <button
                type="button"
                className="focus-visible:outline-ring min-w-0 flex-1 rounded px-2 py-2 text-left focus-visible:outline-2"
                onClick={() => onSelect(step)}
              >
                <span className="font-medium">
                  Step {step.step_order} · Day {step.delay_days} ·{" "}
                  <span className="capitalize">{step.category}</span>
                </span>
                <span className="text-muted-foreground mt-1 block text-xs">
                  {step.media_type === "none"
                    ? "Text"
                    : step.media_type === "image"
                      ? "Image"
                      : "Video"}{" "}
                  · {step.buttons.length} buttons
                </span>
              </button>
              {!readOnly ? (
                <div className="flex">
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    aria-label={`Move step ${step.step_order} up`}
                    disabled={index === 0 || pending}
                    onClick={() => move(index, -1)}
                  >
                    <ArrowUp aria-hidden="true" />
                  </Button>
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    aria-label={`Move step ${step.step_order} down`}
                    disabled={index === steps.length - 1 || pending}
                    onClick={() => move(index, 1)}
                  >
                    <ArrowDown aria-hidden="true" />
                  </Button>
                </div>
              ) : null}
            </li>
          ))}
        </ol>
      ) : (
        <div className="border-border bg-surface-muted mt-4 rounded border border-dashed p-6 text-center">
          <p className="font-medium">No steps yet</p>
          <p className="text-muted-foreground mt-1 text-sm">
            Add the first message in this series.
          </p>
        </div>
      )}
    </section>
  );
}
