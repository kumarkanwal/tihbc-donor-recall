/** Animated incoming bubble shown while TIHBC prepares a response. */
export function TypingIndicator(): React.JSX.Element {
  return (
    <div className="flex justify-start" aria-label="TIHBC is typing">
      <div className="bg-sim-incoming flex items-center gap-1 rounded-[7.5px] px-3 py-3 shadow-sm">
        {[0, 1, 2].map((dot) => (
          <span
            key={dot}
            className="bg-sim-secondary size-1.5 animate-pulse rounded-full"
            style={{ animationDelay: `${dot * 160}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
