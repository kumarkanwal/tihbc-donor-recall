"use client";

import { LayoutGrid, List, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import type {
  SeriesLanguage,
  SeriesKind,
  SeriesStatus,
} from "@/hooks/use-content-series";

export interface SeriesFilters {
  kind: "" | SeriesKind;
  status: "" | SeriesStatus;
  tag: string;
  language: "" | SeriesLanguage;
}

interface SeriesLibraryToolbarProps {
  filters: SeriesFilters;
  view: "table" | "grid";
  onFiltersChange: (filters: SeriesFilters) => void;
  onSearchChange: (search: string) => void;
  onViewChange: (view: "table" | "grid") => void;
}

const selectClass =
  "border-border bg-surface text-foreground rounded-control focus-visible:outline-ring h-10 border px-3 text-sm focus-visible:outline-2";

/** Search, filters, and view control for the content-series library. */
export function SeriesLibraryToolbar({
  filters,
  view,
  onFiltersChange,
  onSearchChange,
  onViewChange,
}: SeriesLibraryToolbarProps): React.JSX.Element {
  const handleSearch = useDebouncedCallback(onSearchChange, 300);
  const update = <Key extends keyof SeriesFilters>(
    key: Key,
    value: SeriesFilters[Key],
  ) => onFiltersChange({ ...filters, [key]: value });

  return (
    <div className="border-border bg-surface rounded-card space-y-3 border p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <label className="relative block w-full lg:max-w-sm">
          <span className="sr-only">Search content series</span>
          <Search
            aria-hidden="true"
            className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2"
          />
          <Input
            type="search"
            className="pl-9"
            placeholder="Search series by name"
            onChange={(event) => handleSearch(event.target.value.trim())}
          />
        </label>
        <div className="flex gap-2" aria-label="Library view">
          <Button
            type="button"
            size="small"
            variant={view === "table" ? "primary" : "secondary"}
            onClick={() => onViewChange("table")}
          >
            <List aria-hidden="true" />
            Table
          </Button>
          <Button
            type="button"
            size="small"
            variant={view === "grid" ? "primary" : "secondary"}
            onClick={() => onViewChange("grid")}
          >
            <LayoutGrid aria-hidden="true" />
            Grid
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <FilterSelect
          label="Filter by kind"
          value={filters.kind}
          onChange={(value) => update("kind", value as SeriesFilters["kind"])}
          options={[
            ["primary", "Primary"],
            ["secondary", "Secondary"],
          ]}
          allLabel="All kinds"
        />
        <FilterSelect
          label="Filter by status"
          value={filters.status}
          onChange={(value) =>
            update("status", value as SeriesFilters["status"])
          }
          options={[
            ["draft", "Draft"],
            ["active", "Active"],
            ["archived", "Archived"],
          ]}
          allLabel="All statuses"
        />
        <FilterSelect
          label="Filter by language"
          value={filters.language}
          onChange={(value) =>
            update("language", value as SeriesFilters["language"])
          }
          options={[
            ["en", "English"],
            ["ur", "Urdu"],
          ]}
          allLabel="All languages"
        />
        <label className="sr-only" htmlFor="series-tag-filter">
          Filter by tag
        </label>
        <Input
          id="series-tag-filter"
          className="w-40"
          value={filters.tag}
          placeholder="Filter by tag"
          onChange={(event) => update("tag", event.target.value)}
        />
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
  allLabel,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: [string, string][];
  allLabel: string;
}): React.JSX.Element {
  return (
    <>
      <label className="sr-only" htmlFor={label.replaceAll(" ", "-")}>
        {label}
      </label>
      <select
        id={label.replaceAll(" ", "-")}
        className={selectClass}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{allLabel}</option>
        {options.map(([key, text]) => (
          <option key={key} value={key}>
            {text}
          </option>
        ))}
      </select>
    </>
  );
}
