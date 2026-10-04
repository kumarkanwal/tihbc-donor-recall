import type { ReactNode } from "react";

interface PhonePreviewProps {
  title?: string;
  children: ReactNode;
}

/** Structural phone frame for series previews and future simulator bubbles. */
export function PhonePreview({
  title = "Message preview",
  children,
}: PhonePreviewProps): React.JSX.Element {
  return (
    <section className="border-foreground bg-surface-muted shadow-surface mx-auto w-full max-w-[360px] rounded-[2rem] border-[6px] p-2">
      <div className="bg-surface overflow-hidden rounded-[1.45rem]">
        <div className="border-border flex h-7 items-center justify-between border-b px-4 text-[0.625rem] font-medium tabular-nums">
          <span>10:30</span>
          <span>TIHBC</span>
        </div>
        <header className="border-border border-b px-4 py-3">
          <h3 className="text-sm font-semibold">{title}</h3>
        </header>
        <div className="min-h-80 p-4">{children}</div>
      </div>
    </section>
  );
}
