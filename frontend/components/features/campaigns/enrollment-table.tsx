"use client";

import { MessageCircle, UserRound } from "lucide-react";
import { useMemo } from "react";

import { DataTable } from "@/components/shared/data-table";
import { createDataTableColumnHelper } from "@/components/shared/data-table-types";
import { DateTime } from "@/components/shared/date-time";
import { MaskedPhone } from "@/components/shared/masked-phone";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import {
  getCampaignErrorMessage,
  type Enrollment,
  type EnrollmentPage,
} from "@/hooks/use-campaigns";
import { openSimulatorChat } from "@/lib/simulator/open-chat";

const columnHelper = createDataTableColumnHelper<Enrollment>();

function currentStep(enrollment: Enrollment): string {
  if (!enrollment.current_series_kind || enrollment.current_step_order === null)
    return "—";
  const series =
    enrollment.current_series_kind === "primary" ? "Primary" : "Secondary";
  return `${series} · Step ${enrollment.current_step_order}`;
}

interface EnrollmentTableProps {
  data?: EnrollmentPage;
  isPending: boolean;
  error: unknown;
  onSearchChange: (search: string) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onDetails: (enrollmentId: string) => void;
  onRetry: () => void;
}

/** Searchable campaign enrollment table with simulator and detail actions. */
export function EnrollmentTable(
  props: EnrollmentTableProps,
): React.JSX.Element {
  const columns = useMemo(
    () =>
      columnHelper.columns([
        columnHelper.display({
          id: "donor",
          header: "Donor",
          cell: ({ row }) => (
            <span className="font-medium">{row.original.donor.full_name}</span>
          ),
        }),
        columnHelper.display({
          id: "phone",
          header: "Phone",
          cell: ({ row }) => (
            <MaskedPhone value={row.original.donor.phone_e164} />
          ),
        }),
        columnHelper.display({
          id: "language",
          header: "Language",
          cell: ({ row }) => row.original.donor.language.toUpperCase(),
        }),
        columnHelper.accessor("status", {
          header: "Status",
          cell: ({ getValue }) => <StatusBadge status={getValue()} />,
        }),
        columnHelper.display({
          id: "current_step",
          header: "Current step",
          cell: ({ row }) => currentStep(row.original),
        }),
        columnHelper.accessor("updated_at", {
          header: "Last activity",
          cell: ({ getValue }) => <DateTime value={getValue()} relative />,
        }),
        columnHelper.display({
          id: "actions",
          header: "Actions",
          cell: ({ row }) => (
            <div
              className="flex gap-1"
              onClick={(event) => event.stopPropagation()}
            >
              <Button
                type="button"
                variant="ghost"
                size="small"
                onClick={() => openSimulatorChat(row.original.donor.id)}
              >
                <MessageCircle aria-hidden="true" />
                View chat
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="small"
                onClick={() => props.onDetails(row.original.id)}
              >
                <UserRound aria-hidden="true" />
                View details
              </Button>
            </div>
          ),
        }),
      ]),
    [props],
  );
  return (
    <DataTable
      columns={columns}
      data={props.data}
      onSearchChange={props.onSearchChange}
      searchPlaceholder="Search donors"
      onPageChange={props.onPageChange}
      onPageSizeChange={props.onPageSizeChange}
      isLoading={props.isPending}
      error={
        props.error
          ? getCampaignErrorMessage(
              props.error,
              "The enrollments could not be loaded.",
            )
          : undefined
      }
      onRetry={props.onRetry}
      emptyTitle="No enrollments"
      emptyDescription="Enrollments appear when this campaign is launched."
    />
  );
}
