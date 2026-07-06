import { CalendarDays, CheckCircle2, CircleAlert, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ActivityRail } from "../components/ActivityRail";
import { AiRecommendations } from "../components/AiRecommendations";
import { GithubSyncCard } from "../components/GithubSyncCard";
import { MonthlyStatsChart } from "../components/MonthlyStatsChart";
import { ProjectHealthList } from "../components/ProjectHealthList";
import { StatCard } from "../components/StatCard";
import { useDashboardSummary } from "../hooks/useDashboardSummary";

const workspaceId = "workspace_platform_engineering";

export default function DashboardPage() {
  const dashboardQuery = useDashboardSummary(workspaceId);

  if (dashboardQuery.isLoading) {
    return (
      <main className="space-y-6 p-5 sm:p-6 lg:p-8">
        <div className="h-28 animate-pulse rounded-lg bg-muted" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-40 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
        <div className="grid gap-5 xl:grid-cols-[1.35fr_0.9fr]">
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
        </div>
      </main>
    );
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center p-6">
        <Card className="max-w-md p-6 text-center">
          <CircleAlert className="mx-auto size-10 text-warning" />
          <h1 className="mt-4 font-display text-2xl font-bold">Dashboard unavailable</h1>
          <p className="mt-2 text-sm leading-6 text-foreground/60">We could not load workspace analytics. Try refreshing the summary.</p>
          <Button className="mt-5" onClick={() => dashboardQuery.refetch()}>
            <RefreshCcw className="size-4" />
            Retry
          </Button>
        </Card>
      </main>
    );
  }

  const summary = dashboardQuery.data;

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-6 top-0 hidden w-16 branch-rail opacity-25 lg:block" aria-hidden="true" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-bold text-foreground/70">
              <span className="size-2 rounded-full bg-success" />
              {summary.workspaceName}
            </div>
            <h1 className="mt-5 max-w-3xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">
              Delivery command center
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-foreground/62 sm:text-base">
              Sprint health, code activity, and AI recommendations for engineering leads who need fast operational signal.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary">
              <CalendarDays className="size-4" />
              {summary.sprintName}
            </Button>
            <Button onClick={() => dashboardQuery.refetch()} disabled={dashboardQuery.isFetching}>
              <RefreshCcw className="size-4" />
              {dashboardQuery.isFetching ? "Refreshing" : "Refresh"}
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {summary.metrics.map((metric) => (
          <StatCard key={metric.id} metric={metric} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.35fr_0.9fr]">
        <div className="space-y-5">
          <MonthlyStatsChart stats={summary.monthlyStats} />
          <ProjectHealthList projects={summary.projects} />
        </div>
        <div className="space-y-5">
          <GithubSyncCard github={summary.github} />
          <AiRecommendations recommendations={summary.recommendations} />
          <Card className="p-5">
            <div className="flex items-start gap-3">
              <div className="flex size-10 items-center justify-center rounded-md bg-success/10 text-success">
                <CheckCircle2 className="size-5" />
              </div>
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Release Readiness</h2>
                <p className="mt-2 text-sm leading-6 text-foreground/60">
                  Core delivery signals are healthy. The only severe risk is the blocked AI planner workstream.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <ActivityRail activity={summary.activity} />
        <Card className="p-5">
          <h2 className="font-display text-xl font-bold tracking-normal">Focus Queue</h2>
          <p className="mt-1 text-sm text-foreground/58">Tasks most likely to improve sprint flow.</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {["Unblock AI-42", "Review KAN-118", "Retest OAuth"].map((item, index) => (
              <div key={item} className="rounded-lg border border-border bg-background p-4">
                <span className="text-xs font-bold text-primary">0{index + 1}</span>
                <p className="mt-3 text-sm font-bold">{item}</p>
                <p className="mt-2 text-xs leading-5 text-foreground/55">Recommended for the next planning sync.</p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </main>
  );
}