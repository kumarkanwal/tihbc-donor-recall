"use client";

import { ChevronDown, Clock3 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCan } from "@/hooks/use-can";
import {
  formatDemoClock,
  useAdvanceDemoClock,
  useDemoClock,
  useResetDemoClock,
} from "@/hooks/use-demo-clock";
import { env } from "@/lib/env";

const skipOptions = [
  { label: "+1 hour", days: 0, hours: 1 },
  { label: "+1 day", days: 1, hours: 0 },
  { label: "+3 days", days: 3, hours: 0 },
  { label: "+7 days", days: 7, hours: 0 },
] as const;

/** Administrator-only demo time display and scheduler advance controls. */
export function DemoClockControl(): React.JSX.Element | null {
  const isAdmin = useCan(["admin"]);
  const clock = useDemoClock(env.NEXT_PUBLIC_DEMO_MODE && isAdmin);
  const advance = useAdvanceDemoClock();
  const reset = useResetDemoClock();

  if (!env.NEXT_PUBLIC_DEMO_MODE || !isAdmin) {
    return null;
  }

  const pending = advance.isPending || reset.isPending;
  const label = clock.data ? formatDemoClock(clock.data.now) : "Loading time";

  return (
    <div className="hidden items-center gap-2 md:flex">
      <span className="text-muted-foreground hidden max-w-44 truncate text-xs xl:block xl:max-w-none">
        {label}
      </span>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="secondary"
            disabled={pending || clock.isPending || Boolean(clock.error)}
          >
            <Clock3 aria-hidden="true" strokeWidth={1.75} />
            Skip time
            <ChevronDown aria-hidden="true" strokeWidth={1.75} />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-44">
          {skipOptions.map((option) => (
            <DropdownMenuItem
              key={option.label}
              onSelect={() =>
                advance.mutate({ days: option.days, hours: option.hours })
              }
            >
              {option.label}
            </DropdownMenuItem>
          ))}
          <DropdownMenuItem onSelect={() => reset.mutate()}>
            Reset clock
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
