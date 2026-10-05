import { AlertTriangle } from "lucide-react";

import type { CampaignLaunchProblem } from "@/hooks/use-campaigns";

const fieldLabels: Record<string, string> = {
  batch_id: "Donor batch",
  primary_series_id: "Primary series",
  secondary_series_id: "Secondary series",
};

/** Aggregate backend launch problems with actionable field labels. */
export function LaunchProblems({
  problems,
}: {
  problems: CampaignLaunchProblem[];
}): React.JSX.Element | null {
  if (problems.length === 0) return null;
  return (
    <section
      role="alert"
      className="border-danger/30 bg-danger/10 text-danger rounded-card border p-4"
    >
      <h2 className="flex items-center gap-2 font-semibold">
        <AlertTriangle aria-hidden="true" className="size-4" />
        Campaign cannot be launched
      </h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
        {problems.map((problem, index) => (
          <li key={`${problem.field}-${index}`}>
            <span className="font-medium">
              {fieldLabels[problem.field] ?? problem.field}:
            </span>{" "}
            {problem.reason}
          </li>
        ))}
      </ul>
    </section>
  );
}
