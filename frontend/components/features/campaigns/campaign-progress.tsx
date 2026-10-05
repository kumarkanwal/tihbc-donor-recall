/** Compact responded/enrolled campaign progress display. */
export function CampaignProgress({
  responded,
  enrolled,
}: {
  responded: number;
  enrolled: number;
}): React.JSX.Element {
  const percentage =
    enrolled > 0 ? Math.min(100, (responded / enrolled) * 100) : 0;
  return (
    <div
      className="min-w-32"
      aria-label={`${responded} of ${enrolled} responded`}
    >
      <div className="bg-surface-muted h-2 overflow-hidden rounded-full">
        <div
          className="bg-primary h-full rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-muted-foreground mt-1 text-xs tabular-nums">
        {responded} / {enrolled}
      </p>
    </div>
  );
}
