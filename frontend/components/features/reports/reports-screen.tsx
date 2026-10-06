"use client";

import { Download } from "lucide-react";
import { useMemo, useState } from "react";

import { MetricsFilters } from "@/components/shared/metrics-filters";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { useCampaignCatalog } from "@/hooks/use-campaigns";
import { useExportReport, type ReportExport } from "@/hooks/use-metrics";
import type { MetricsFilters as MetricsFilterValues } from "@/lib/api/contracts";

import { DeliveryReport } from "./delivery-report";
import { InactiveNumbersReport } from "./inactive-numbers-report";
import { ReportTabs, type ReportTab } from "./report-tabs";
import { ResponsesReport } from "./responses-report";

const exportByTab: Record<ReportTab, ReportExport> = {
  delivery: "campaigns",
  responses: "response-breakdown",
  inactive: "inactive-numbers",
};

/** Filtered reports workspace with a CSV export for each contract report. */
export function ReportsScreen(): React.JSX.Element {
  const [tab, setTab] = useState<ReportTab>("delivery");
  const [campaignId, setCampaignId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const filters = useMemo<MetricsFilterValues>(
    () => ({
      campaign_id: campaignId || undefined,
      from: from || undefined,
      to: to || undefined,
    }),
    [campaignId, from, to],
  );
  const campaigns = useCampaignCatalog(undefined);
  const exportMutation = useExportReport(exportByTab[tab], filters);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="Review delivery, engagement, responses, and inactive-number results."
        actions={
          <Button
            type="button"
            variant="secondary"
            disabled={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            <Download aria-hidden="true" />
            Export CSV
          </Button>
        }
      />
      <ReportTabs value={tab} onChange={setTab} />
      <MetricsFilters
        campaignId={campaignId}
        from={from}
        to={to}
        campaigns={
          campaigns.data?.items.map(({ id, name }) => ({ id, name })) ?? []
        }
        onCampaignChange={setCampaignId}
        onFromChange={setFrom}
        onToChange={setTo}
      />
      {tab === "delivery" ? <DeliveryReport filters={filters} /> : null}
      {tab === "responses" ? <ResponsesReport filters={filters} /> : null}
      {tab === "inactive" ? (
        <InactiveNumbersReport
          key={`${campaignId}-${from}-${to}`}
          filters={filters}
        />
      ) : null}
      {exportMutation.error ? (
        <p role="alert" className="text-danger text-sm">
          The report export could not be created.
        </p>
      ) : null}
    </div>
  );
}
