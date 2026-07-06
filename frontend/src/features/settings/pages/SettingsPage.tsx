import { AlertTriangle, Moon, RefreshCcw, Settings, ShieldCheck, Sun, UsersRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useUiStore } from "@/store/ui.store";
import { AuditLogPanel } from "../components/AuditLogPanel";
import { InviteMemberForm } from "../components/InviteMemberForm";
import { MembersTable } from "../components/MembersTable";
import { WorkspaceSettingsForm } from "../components/WorkspaceSettingsForm";
import { useSettingsSummary } from "../hooks/useSettingsSummary";

const workspaceId = "workspace_platform_engineering";

export default function SettingsPage() {
  const settingsQuery = useSettingsSummary(workspaceId);
  const theme = useUiStore((state) => state.theme);
  const setTheme = useUiStore((state) => state.setTheme);

  if (settingsQuery.isLoading) {
    return (
      <main className="space-y-6 p-5 sm:p-6 lg:p-8">
        <div className="h-44 animate-pulse rounded-lg bg-muted" />
        <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
        </div>
      </main>
    );
  }

  if (settingsQuery.isError || !settingsQuery.data) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center p-6">
        <Card className="max-w-md p-6 text-center">
          <AlertTriangle className="mx-auto size-10 text-warning" />
          <h1 className="mt-4 font-display text-2xl font-bold tracking-normal">Settings unavailable</h1>
          <p className="mt-2 text-sm leading-6 text-foreground/60">Workspace settings could not be loaded.</p>
          <Button className="mt-5" onClick={() => settingsQuery.refetch()}>
            <RefreshCcw className="size-4" />
            Retry
          </Button>
        </Card>
      </main>
    );
  }

  const summary = settingsQuery.data;
  const activeMembers = summary.members.filter((member) => member.status === "active").length;
  const admins = summary.members.filter((member) => member.role === "owner" || member.role === "admin").length;

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-7 top-0 hidden w-16 branch-rail opacity-20 lg:block" aria-hidden="true" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-bold text-primary">
              <Settings className="size-4" />
              Workspace Settings
            </div>
            <h1 className="mt-5 max-w-4xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">
              Control access, defaults, and operating posture.
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-foreground/62 sm:text-base">
              Manage workspace identity, invite teammates, set role boundaries, and keep audit signals visible.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 lg:min-w-[390px]">
            <div className="rounded-lg border border-border bg-background p-3">
              <UsersRound className="size-4 text-primary" />
              <p className="mt-2 text-2xl font-bold">{summary.members.length}</p>
              <p className="text-xs font-semibold text-foreground/50">Members</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <ShieldCheck className="size-4 text-success" />
              <p className="mt-2 text-2xl font-bold">{admins}</p>
              <p className="text-xs font-semibold text-foreground/50">Admins</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <RefreshCcw className="size-4 text-warning" />
              <p className="mt-2 text-2xl font-bold">{activeMembers}</p>
              <p className="text-xs font-semibold text-foreground/50">Active</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <div className="space-y-5">
          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Workspace Defaults</h2>
            <p className="mt-1 text-sm text-foreground/58">These settings map to organization-level backend controls.</p>
            <div className="mt-5">
              <WorkspaceSettingsForm workspaceId={workspaceId} workspace={summary.workspace} />
            </div>
          </Card>
          <MembersTable members={summary.members} />
        </div>

        <aside className="space-y-5">
          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Invite Member</h2>
            <p className="mt-1 text-sm text-foreground/58">Send a role-scoped workspace invitation.</p>
            <div className="mt-5">
              <InviteMemberForm workspaceId={workspaceId} />
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Theme</h2>
            <p className="mt-1 text-sm text-foreground/58">Switch the command center palette.</p>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <Button type="button" variant={theme === "light" ? "primary" : "secondary"} onClick={() => setTheme("light")}>
                <Sun className="size-4" />
                Light
              </Button>
              <Button type="button" variant={theme === "dark" ? "primary" : "secondary"} onClick={() => setTheme("dark")}>
                <Moon className="size-4" />
                Dark
              </Button>
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Security Posture</h2>
            <p className="mt-2 text-sm leading-6 text-foreground/60">
              AI features are {summary.workspace.aiEnabled ? "enabled" : "disabled"}; GitHub linkage is {summary.workspace.githubRequired ? "required" : "optional"} for delivery metadata.
            </p>
            <div className="mt-4 h-2 rounded-full bg-muted">
              <div className="h-2 rounded-full bg-success" style={{ width: `${summary.workspace.githubRequired ? 88 : 62}%` }} />
            </div>
          </Card>
        </aside>
      </section>

      <AuditLogPanel events={summary.auditEvents} />
    </main>
  );
}