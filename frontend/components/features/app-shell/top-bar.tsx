"use client";

import { Bell, ChevronDown, LogOut } from "lucide-react";
import { usePathname } from "next/navigation";

import { ThemeSwitch } from "@/components/shared/theme-switch";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useLogout } from "@/hooks/use-logout";
import { getNavigationItem } from "@/lib/navigation";

import { DemoClockControl } from "./demo-clock-control";

/** Current page context and application-level controls. */
export function TopBar(): React.JSX.Element {
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const currentItem = getNavigationItem(pathname);

  return (
    <header className="border-border bg-surface sticky top-0 z-30 flex min-h-20 items-center justify-between gap-4 border-b px-4 py-3 sm:px-6">
      <div className="min-w-0">
        <p className="text-muted-foreground truncate text-xs">
          Donor Recall / {currentItem.label}
        </p>
        <p className="truncate text-lg font-semibold">{currentItem.label}</p>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <DemoClockControl />

        <Button
          type="button"
          variant="secondary"
          size="icon"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell aria-hidden="true" strokeWidth={1.75} />
        </Button>
        <ThemeSwitch />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button type="button" variant="secondary">
              <span className="hidden text-left sm:block">
                <span className="block text-xs font-medium">
                  {user?.full_name ?? "Staff user"}
                </span>
                <span className="text-muted-foreground block text-xs capitalize">
                  {user?.role ?? "coordinator"}
                </span>
              </span>
              <ChevronDown aria-hidden="true" strokeWidth={1.75} />
              <span className="sr-only">Open user menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onSelect={logout}>
              <LogOut aria-hidden="true" strokeWidth={1.75} />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
