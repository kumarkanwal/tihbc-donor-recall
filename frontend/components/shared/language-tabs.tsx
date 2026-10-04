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
  languages?: LanguageCode[];
}

/** Switch between equivalent English and Urdu content. */
export function LanguageTabs({
  english,
  urdu,
  value,
  onValueChange,
  className,
  languages = ["en", "ur"],
}: LanguageTabsProps): React.JSX.Element {
  const defaultLanguage = languages[0] ?? "en";
  return (
    <Tabs.Root
      defaultValue={defaultLanguage}
      value={value}
      onValueChange={(nextValue) => onValueChange?.(nextValue as LanguageCode)}
      className={className}
    >
      <Tabs.List
        aria-label="Content language"
        className="bg-surface-muted rounded-control inline-flex p-1"
      >
        {languages.map((language) => (
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
      {languages.includes("en") ? (
        <Tabs.Content
          value="en"
          className="mt-4 focus-visible:outline-none"
          lang="en"
        >
          {english}
        </Tabs.Content>
      ) : null}
      {languages.includes("ur") ? (
        <Tabs.Content
          value="ur"
          className="mt-4 focus-visible:outline-none"
          lang="ur"
          dir="rtl"
        >
          {urdu}
        </Tabs.Content>
      ) : null}
    </Tabs.Root>
  );
}
