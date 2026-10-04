"use client";

import * as Tabs from "@radix-ui/react-tabs";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils/class-names";

export type LanguageCode = "en" | "ur";

interface LanguageTabsProps {
  english: ReactNode;
  urdu: ReactNode;
  value?: LanguageCode;
  onValueChange?: (language: LanguageCode) => void;
  className?: string;
}

/** Switch between equivalent English and Urdu content. */
export function LanguageTabs({
  english,
  urdu,
  value,
  onValueChange,
  className,
}: LanguageTabsProps): React.JSX.Element {
  return (
    <Tabs.Root
      defaultValue="en"
      value={value}
      onValueChange={(nextValue) => onValueChange?.(nextValue as LanguageCode)}
      className={className}
    >
      <Tabs.List
        aria-label="Content language"
        className="bg-surface-muted rounded-control inline-flex p-1"
      >
        {(["en", "ur"] as const).map((language) => (
          <Tabs.Trigger
            key={language}
            value={language}
            className={cn(
              "rounded-control focus-visible:outline-ring min-h-9 px-4 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2",
              "text-muted-foreground data-[state=active]:bg-surface data-[state=active]:text-foreground data-[state=active]:shadow-surface",
            )}
          >
            {language === "en" ? "English" : "Urdu"}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
      <Tabs.Content
        value="en"
        className="mt-4 focus-visible:outline-none"
        lang="en"
      >
        {english}
      </Tabs.Content>
      <Tabs.Content
        value="ur"
        className="mt-4 focus-visible:outline-none"
        lang="ur"
        dir="rtl"
      >
        {urdu}
      </Tabs.Content>
    </Tabs.Root>
  );
}
