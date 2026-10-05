"use client";

import * as Tabs from "@radix-ui/react-tabs";

import { PageHeader } from "@/components/shared/page-header";
import { useCan } from "@/hooks/use-can";
import { env } from "@/lib/env";

import { DemoSettings } from "./demo-settings";
import { IntegrationSettings } from "./integration-settings";
import { SettingsTabTrigger } from "./settings-tab-trigger";
import { UsersSettings } from "./users-settings";

/** Read-only integration and user settings plus admin demo controls. */
export function SettingsScreen(): React.JSX.Element {
  const canManageDemo = useCan(["admin"]) && env.NEXT_PUBLIC_DEMO_MODE;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="View integration, user, and demo environment settings."
      />
      <Tabs.Root defaultValue="integration">
        <Tabs.List
          aria-label="Settings sections"
          className="border-border flex overflow-x-auto border-b"
        >
          <SettingsTabTrigger value="integration">
            WhatsApp integration
          </SettingsTabTrigger>
          <SettingsTabTrigger value="users">Users</SettingsTabTrigger>
          {canManageDemo ? (
            <SettingsTabTrigger value="demo">Demo controls</SettingsTabTrigger>
          ) : null}
        </Tabs.List>
        <Tabs.Content
          value="integration"
          className="mt-6 focus-visible:outline-none"
        >
          <IntegrationSettings />
        </Tabs.Content>
        <Tabs.Content value="users" className="mt-6 focus-visible:outline-none">
          <UsersSettings />
        </Tabs.Content>
        {canManageDemo ? (
          <Tabs.Content
            value="demo"
            className="mt-6 focus-visible:outline-none"
          >
            <DemoSettings />
          </Tabs.Content>
        ) : null}
      </Tabs.Root>
    </div>
  );
}
