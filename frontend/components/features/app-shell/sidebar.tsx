"use client";

import {
  BarChart3,
  FolderHeart,
  Gauge,
  Inbox,
  Megaphone,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  UsersRound,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/class-names";
import { useUiStore } from "@/lib/stores/ui-store";

const items = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/batches", label: "Donor Batches", icon: UsersRound },
  { href: "/series", label: "Content Series", icon: FolderHeart },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/inbox", label: "Follow-up Inbox", icon: Inbox },
  { href: "/reports", label: "Reports", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

function isActiveRoute(pathname: string, href: string): boolean {
  return pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));
}

/** Persistent, responsive application navigation. */
export function Sidebar(): React.JSX.Element {
  const pathname = usePathname();
  const isCollapsed = useUiStore((state) => state.isSidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <aside
      className={cn(
        "border-border bg-surface sticky top-0 flex h-screen shrink-0 flex-col border-r transition-[width] duration-200 max-lg:w-16",
        isCollapsed ? "w-16" : "w-60",
      )}
    >
      <div className="border-border flex h-20 items-center border-b px-2">
        <Link
          href="/"
          className="focus-visible:outline-ring mx-auto flex items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2"
          aria-label="Donor Recall dashboard"
        >
          <span className="block shrink-0 rounded-lg bg-white p-1.5">
            <Image
              src="/images/IHHN-Logo-02-150x150.webp"
              alt=""
              width={isCollapsed ? 40 : 48}
              height={isCollapsed ? 40 : 48}
              priority
            />
          </span>
          <span
            className={cn(
              "text-sm font-semibold whitespace-nowrap max-lg:hidden",
              isCollapsed && "hidden",
            )}
          >
            Donor Recall
          </span>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-2" aria-label="Primary navigation">
        {items.map(({ href, label, icon: Icon }) => {
          const isActive = isActiveRoute(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              title={isCollapsed ? label : undefined}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "focus-visible:outline-ring rounded-control relative flex h-10 items-center gap-3 px-3 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 max-lg:justify-center max-lg:px-0",
                isActive
                  ? "bg-primary-soft text-primary before:bg-accent before:absolute before:inset-y-1 before:left-0 before:w-[3px] before:rounded-r"
                  : "text-muted-foreground hover:bg-surface-muted hover:text-foreground",
                isCollapsed && "justify-center px-0",
              )}
            >
              <Icon
                aria-hidden="true"
                className="size-5 shrink-0"
                strokeWidth={1.75}
              />
              <span className={cn("max-lg:hidden", isCollapsed && "hidden")}>
                {label}
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="border-border border-t p-2 max-lg:hidden">
        <Button
          type="button"
          variant="ghost"
          className={cn("w-full", isCollapsed ? "px-0" : "justify-start")}
          onClick={toggleSidebar}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <PanelLeftOpen aria-hidden="true" strokeWidth={1.75} />
          ) : (
            <PanelLeftClose aria-hidden="true" strokeWidth={1.75} />
          )}
          {!isCollapsed ? "Collapse" : null}
        </Button>
      </div>
    </aside>
  );
}
