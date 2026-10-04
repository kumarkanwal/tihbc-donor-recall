export interface NavigationItem {
  href: string;
  label: string;
}

export const navigationItems = [
  { href: "/", label: "Dashboard" },
  { href: "/batches", label: "Donor Batches" },
  { href: "/series", label: "Content Series" },
  { href: "/campaigns", label: "Campaigns" },
  { href: "/inbox", label: "Follow-up Inbox" },
  { href: "/reports", label: "Reports" },
  { href: "/settings", label: "Settings" },
] as const satisfies readonly NavigationItem[];

/** Resolve shell metadata for a pathname, including nested feature routes. */
export function getNavigationItem(pathname: string): NavigationItem {
  return (
    [...navigationItems]
      .sort((left, right) => right.href.length - left.href.length)
      .find(
        ({ href }) =>
          pathname === href ||
          (href !== "/" && pathname.startsWith(`${href}/`)),
      ) ?? navigationItems[0]
  );
}
