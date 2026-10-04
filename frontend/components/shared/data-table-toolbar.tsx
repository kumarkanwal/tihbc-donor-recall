"use client";

import { Search } from "lucide-react";
import type { ReactNode } from "react";

import { Input } from "@/components/ui/input";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";

interface DataTableToolbarProps {
  onSearchChange?: (search: string) => void;
  searchPlaceholder: string;
  filterSlot?: ReactNode;
}

/** Debounced search and caller-provided filters for a data table. */
export function DataTableToolbar({
  onSearchChange,
  searchPlaceholder,
  filterSlot,
}: DataTableToolbarProps): React.JSX.Element {
  const handleSearch = useDebouncedCallback(
    (value: string) => onSearchChange?.(value),
    300,
  );

  return (
    <div className="border-border flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center sm:justify-between">
      <label className="relative block w-full sm:max-w-sm">
        <span className="sr-only">Search table</span>
        <Search
          aria-hidden="true"
          className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
          strokeWidth={1.75}
        />
        <Input
          type="search"
          placeholder={searchPlaceholder}
          className="pl-9"
          onChange={(event) => handleSearch(event.target.value)}
        />
      </label>
      {filterSlot ? (
        <div className="flex flex-wrap gap-2">{filterSlot}</div>
      ) : null}
    </div>
  );
}
