/** Centered date marker in a conversation. */
export function DateSeparator({ label }: { label: string }): React.JSX.Element {
  return (
    <div className="flex justify-center py-2">
      <span className="bg-sim-date-chip text-sim-date-text rounded-md px-2.5 py-1 text-[0.65rem] shadow-sm">
        {label}
      </span>
    </div>
  );
}
