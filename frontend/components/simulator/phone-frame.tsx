import Image from "next/image";
import type { ReactNode } from "react";

interface SimulatorPhoneFrameProps {
  title?: string;
  children: ReactNode;
}

/** Light-theme phone frame shared by content previews and the simulator. */
export function SimulatorPhoneFrame({
  title = "Team Indus Health & Blood Center",
  children,
}: SimulatorPhoneFrameProps): React.JSX.Element {
  return (
    <section className="border-foreground bg-sim-wallpaper mx-auto w-full max-w-[360px] overflow-hidden rounded-[2rem] border-[6px] font-sans shadow-lg">
      <div className="bg-sim-incoming text-sim-text flex h-7 items-center justify-between px-5 text-[0.625rem] font-medium tabular-nums">
        <span>10:30</span>
        <span>TIHBC</span>
      </div>
      <header className="bg-sim-header text-sim-header-text flex items-center gap-3 px-3 py-2.5">
        <span className="bg-sim-incoming flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-full p-1">
          <Image
            src="/images/IHHN-Logo-02-150x150.webp"
            alt=""
            width={32}
            height={32}
          />
        </span>
        <div className="min-w-0">
          <h3 className="truncate text-[0.78rem] font-semibold">{title}</h3>
          <p className="text-[0.65rem] opacity-90">Business account</p>
        </div>
      </header>
      <div className="bg-sim-wallpaper min-h-[440px] p-3">{children}</div>
    </section>
  );
}
