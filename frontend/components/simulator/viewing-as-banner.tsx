import { MaskedPhone } from "@/components/shared/masked-phone";
import type { SimulatorDonor } from "@/lib/simulator";

/** Presenter context outside the donor's phone frame. */
export function ViewingAsBanner({
  donor,
}: {
  donor: SimulatorDonor;
}): React.JSX.Element {
  return (
    <div className="border-border bg-primary-soft text-foreground mx-auto mb-2 flex max-w-[360px] flex-wrap items-center justify-center gap-1 rounded-md border px-3 py-2 text-xs">
      <span>Viewing as: {donor.name}</span>
      <span aria-hidden="true">(</span>
      <MaskedPhone value={donor.phone} />
      <span aria-hidden="true">)</span>
    </div>
  );
}
