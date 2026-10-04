"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  SeriesSettingsForm,
  toSeriesInput,
  type SeriesSettingsValues,
} from "@/components/features/series/series-settings-form";
import { SimulatorPhoneFrame } from "@/components/simulator/phone-frame";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { useCan } from "@/hooks/use-can";
import { useCreateContentSeries } from "@/hooks/use-content-series";

/** Create a draft series before adding ordered steps. */
export function SeriesNewScreen(): React.JSX.Element {
  const canCreate = useCan(["admin"]);
  const router = useRouter();
  const createSeries = useCreateContentSeries();

  if (!canCreate) {
    return (
      <ErrorState
        title="Administrator access required"
        description="Only administrators can create content series."
      />
    );
  }

  async function submit(values: SeriesSettingsValues): Promise<void> {
    try {
      const series = await createSeries.mutateAsync(toSeriesInput(values));
      router.push(`/series/${series.id}`);
    } catch {
      // The mutation error is rendered inline.
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="New content series"
        description="Create the draft, then add bilingual message steps."
        breadcrumb={<Link href="/series">Content Series</Link>}
      />
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
        <SeriesSettingsForm
          pending={createSeries.isPending}
          error={createSeries.error}
          submitLabel="Create series"
          onSubmit={(values) => void submit(values)}
        />
        <div className="xl:sticky xl:top-24">
          <SimulatorPhoneFrame>
            <div className="bg-sim-date-chip text-sim-date-text mx-auto w-fit rounded px-3 py-1 text-[0.65rem] shadow-sm">
              Message preview
            </div>
            <p className="text-sim-secondary mt-28 text-center text-xs">
              Add a step after creating the series to see its preview.
            </p>
          </SimulatorPhoneFrame>
        </div>
      </div>
    </div>
  );
}
