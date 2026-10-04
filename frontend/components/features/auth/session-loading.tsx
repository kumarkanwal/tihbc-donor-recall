/** Full-page loading state used while resolving browser authentication. */
export function SessionLoading(): React.JSX.Element {
  return (
    <main
      className="flex min-h-screen items-center justify-center p-6"
      aria-busy="true"
    >
      <div className="w-full max-w-sm space-y-3" aria-label="Checking session">
        <div className="bg-surface-muted rounded-card mx-auto size-16 animate-pulse" />
        <div className="bg-surface-muted mx-auto h-5 w-40 animate-pulse rounded" />
        <div className="bg-surface-muted mx-auto h-4 w-56 animate-pulse rounded" />
      </div>
    </main>
  );
}
