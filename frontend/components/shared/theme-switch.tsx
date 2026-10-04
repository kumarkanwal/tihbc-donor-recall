"use client";

import { Laptop, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useHasMounted } from "@/hooks/use-has-mounted";

const themes = [
  { label: "Light", value: "light", icon: Sun },
  { label: "Dark", value: "dark", icon: Moon },
  { label: "System", value: "system", icon: Laptop },
] as const;

/** Select and persist the application color theme. */
export function ThemeSwitch(): React.JSX.Element {
  const hasMounted = useHasMounted();
  const { theme, setTheme } = useTheme();

  const activeTheme = hasMounted ? (theme ?? "light") : "light";
  const activeOption =
    themes.find((option) => option.value === activeTheme) ?? themes[0];
  const ActiveIcon = activeOption.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" aria-label="Choose color theme">
          <ActiveIcon aria-hidden="true" strokeWidth={1.75} />
          {activeOption.label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" aria-label="Color theme">
        <DropdownMenuRadioGroup value={activeTheme} onValueChange={setTheme}>
          {themes.map(({ label, value, icon: Icon }) => (
            <DropdownMenuRadioItem key={value} value={value}>
              <Icon aria-hidden="true" strokeWidth={1.75} />
              {label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
