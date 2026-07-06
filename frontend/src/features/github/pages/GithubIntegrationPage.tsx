import { AlertTriangle, Github, GitPullRequestArrow, RadioTower, RefreshCcw, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CommitFeed } from "../components/CommitFeed";
import { GithubConnectionCard } from "../components/GithubConnectionCard";
import { IssueList } from "../components/IssueList";
import { PullRequestList } from "../components/PullRequestList";
import { RepositoryList } from "../components/RepositoryList";
import { useGithubConnect } from "../hooks/useGithubConnect";
import { useGithubSummary } from "../hooks/useGithubSummary";
import { useGithubSync } from "../hooks/useGithubSync";

const workspaceId = "workspace_platform_engineering";

export default function GithubIntegrationPage() {
  const summaryQuery = useGithubSummary(workspaceId);
  const connectMutation = useGithubConnect(workspaceId);
  const syncMutation = useGithubSync(workspaceId);

  if (summaryQuery.isLoading) {
    return (
      <main className="space-y-6 p-5 sm:p-6 lg:p-8">
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
        <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
        </div>
      </main>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center p-6">
        <Card className="max-w-md p-6 text-center">
          <AlertTriangle className="mx-auto size-10 text-warning" />
          <h1 className="mt-4 font-display text-2xl font-bold tracking-normal">GitHub unavailable</h1>
          <p className="mt-2 text-sm leading-6 text-foreground/60">The integration summary could not be loaded.</p>
          <Button className="mt-5" onClick={() => summaryQuery.refetch()}>
            <RefreshCcw className="size-4" />
            Retry
          </Button>
        </Card>
      </main>
    );
  }

  const summary = summaryQuery.data;
  const openIssues = summary.issues.filter((issue) => issue.state === "open").length;
  const openPullRequests = summary.pullRequests.filter((pullRequest) => pullRequest.state === "open" || pullRequest.state === "draft").length;
  const commitsToday = summary.repositories.reduce((sum, repository) => sum + repository.commitsToday, 0);

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-7 top-0 hidden w-16 branch-rail opacity-20 lg:block" aria-hidden="true" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-bold text-foreground">
              <Github className="size-4" />
              GitHub Integration
            </div>
            <h1 className="mt-5 max-w-4xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">
              Code metadata connected to delivery decisions.
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-foreground/62 sm:text-base">
              OAuth connection, repository sync, commits, issues, and pull requests in one operational view.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 lg:min-w-[390px]">
            <div className="rounded-lg border border-border bg-background p-3">
              <Github className="size-4 text-foreground" />
              <p className="mt-2 text-2xl font-bold">{summary.repositories.length}</p>
              <p className="text-xs font-semibold text-foreground/50">Repos</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <GitPullRequestArrow className="size-4 text-primary" />
              <p className="mt-2 text-2xl font-bold">{openPullRequests}</p>
              <p className="text-xs font-semibold text-foreground/50">Open PRs</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <RadioTower className="size-4 text-success" />
              <p className="mt-2 text-2xl font-bold">{commitsToday}</p>
              <p className="text-xs font-semibold text-foreground/50">Commits</p>
            </div>
          </div>
        </div>
      </section>

      <GithubConnectionCard
        connection={summary.connection}
        isConnecting={connectMutation.isPending}
        isSyncing={syncMutation.isPending}
        onConnect={() => connectMutation.mutate()}
        onSync={() => syncMutation.mutate()}
      />

      {(connectMutation.isError || syncMutation.isError) ? (
        <Card className="border-warning/40 bg-warning/10 p-4 text-sm font-semibold text-warning">
          GitHub action failed. Check OAuth configuration and try again.
        </Card>
      ) : null}

      <section className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <div className="space-y-5">
          <RepositoryList repositories={summary.repositories} />
          <div className="grid gap-5 2xl:grid-cols-2">
            <IssueList issues={summary.issues} />
            <PullRequestList pullRequests={summary.pullRequests} />
          </div>
        </div>
        <aside className="space-y-5">
          <CommitFeed commits={summary.commits} />
          <Card className="p-5">
            <div className="flex items-start gap-3">
              <div className="flex size-10 items-center justify-center rounded-md bg-success/10 text-success">
                <ShieldCheck className="size-5" />
              </div>
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Security Posture</h2>
                <p className="mt-2 text-sm leading-6 text-foreground/60">
                  Tokens are encrypted server-side. OAuth state uses PKCE and short-lived verification before metadata sync begins.
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Triage Signal</h2>
            <p className="mt-2 text-sm leading-6 text-foreground/60">
              {openIssues} open issues and {openPullRequests} active pull requests are ready to link into project planning.
            </p>
            <div className="mt-4 h-2 rounded-full bg-muted">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(100, openIssues * 8)}%` }} />
            </div>
          </Card>
        </aside>
      </section>
    </main>
  );
}