"use client";

import * as Tabs from "@radix-ui/react-tabs";

/** Consistent accessible tab trigger for the Settings workspace. */
export function SettingsTabTrigger({
  value,
  children,
}: {
  value: string;
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <Tabs.Trigger
      value={value}
      className="text-muted-foreground border-primary focus-visible:outline-ring data-[state=active]:text-primary -mb-px border-b-2 border-transparent px-4 py-3 text-sm font-medium whitespace-nowrap focus-visible:outline-2 data-[state=active]:border-current"
    >
      {children}
    </Tabs.Trigger>
  );
}
