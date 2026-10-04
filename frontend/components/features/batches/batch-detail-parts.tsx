"use client";

import * as Tabs from "@radix-ui/react-tabs";

export type DetailTab = "donors" | "validation";

export function BatchTabTrigger({
  value,
  children,
}: {
  value: DetailTab;
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <Tabs.Trigger
      value={value}
      className="text-muted-foreground border-primary focus-visible:outline-ring data-[state=active]:text-primary -mb-px border-b-2 border-transparent px-4 py-3 text-sm font-medium focus-visible:outline-2 data-[state=active]:border-current"
    >
      {children}
    </Tabs.Trigger>
  );
}

export function DonorFilters({
  segments,
  segment,
  language,
  onSegmentChange,
  onLanguageChange,
}: {
  segments: string[];
  segment: string;
  language: "" | "en" | "ur";
  onSegmentChange: (value: string) => void;
  onLanguageChange: (value: "" | "en" | "ur") => void;
}): React.JSX.Element {
  const selectClass =
    "border-border bg-surface text-foreground rounded-control focus-visible:outline-ring h-10 border px-3 text-sm focus-visible:outline-2";
  return (
    <>
      <label className="sr-only" htmlFor="segment-filter">
        Filter by segment
      </label>
      <select
        id="segment-filter"
        className={selectClass}
        value={segment}
        onChange={(event) => onSegmentChange(event.target.value)}
      >
        <option value="">All segments</option>
        {segments.map((value) => (
          <option key={value} value={value}>
            {value.replaceAll("_", " ")}
          </option>
        ))}
      </select>
      <label className="sr-only" htmlFor="language-filter">
        Filter by language
      </label>
      <select
        id="language-filter"
        className={selectClass}
        value={language}
        onChange={(event) =>
          onLanguageChange(event.target.value as "" | "en" | "ur")
        }
      >
        <option value="">All languages</option>
        <option value="en">English</option>
        <option value="ur">Urdu</option>
      </select>
    </>
  );
}

export function DetailLoading(): React.JSX.Element {
  return (
    <div className="space-y-6" aria-label="Loading donor batch">
      <div className="bg-surface-muted rounded-card h-20 animate-pulse" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((value) => (
          <div
            key={value}
            className="border-border bg-surface rounded-card h-32 animate-pulse border"
          />
        ))}
      </div>
    </div>
  );
}
