import { AlertTriangle, ArrowLeft, Bot, CalendarDays, ExternalLink, GitBranch, KanbanSquare, RefreshCcw, UsersRound } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import { ProjectAiNotes } from "../components/ProjectAiNotes";
import { ProjectCommitFeed } from "../components/ProjectCommitFeed";
import { ProjectMilestoneRail } from "../components/ProjectMilestoneRail";
import { ProjectTaskPreviewTable } from "../components/ProjectTaskPreviewTable";
import { useProject } from "../hooks/useProject";

const workspaceId = "workspace_platform_engineering";

const statusClass = {
  planned: "bg-muted text-foreground/70",
  active: "bg-primary/10 text-primary",
  on_hold: "bg-accent/10 text-accent",
  completed: "bg-success/10 text-success",
  at_risk: "bg-warning/10 text-warning",
};

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId ?? "project_core_api";
  const projectQuery = useProject(workspaceId, projectId);

  if (projectQuery.isLoading) {
    return (
      <main className="space-y-6 p-5 sm:p-6 lg:p-8">
        <div className="h-56 animate-pulse rounded-lg bg-muted" />
        <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
          <div className="h-96 animate-pulse rounded-lg bg-muted" />
        </div>
      </main>
    );
  }

  if (projectQuery.isError || !projectQuery.data) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center p-6">
        <Card className="max-w-md p-6 text-center">
          <AlertTriangle className="mx-auto size-10 text-warning" />
          <h1 className="mt-4 font-display text-2xl font-bold tracking-normal">Project unavailable</h1>
          <p className="mt-2 text-sm leading-6 text-foreground/60">This project could not be loaded from the workspace.</p>
          <Button className="mt-5" onClick={() => projectQuery.refetch()}>
            <RefreshCcw className="size-4" />
            Retry
          </Button>
        </Card>
      </main>
    );
  }

  const project = projectQuery.data;

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-7 top-0 hidden w-16 branch-rail opacity-20 lg:block" aria-hidden="true" />
        <div className="relative space-y-6">
          <Link className="inline-flex items-center gap-2 text-sm font-bold text-foreground/58 transition hover:text-primary" to="/app/projects">
            <ArrowLeft className="size-4" />
            Back to projects
          </Link>

          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-muted px-2 py-1 text-xs font-black text-foreground/70">{project.key}</span>
                <span className={cn("rounded px-2 py-1 text-xs font-black capitalize", statusClass[project.status])}>{project.status.replace("_", " ")}</span>
                <span className="rounded bg-background px-2 py-1 text-xs font-black capitalize text-accent">{project.priority} priority</span>
              </div>
              <h1 className="mt-5 max-w-4xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">{project.name}</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-foreground/62 sm:text-base">{project.description}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link to={`/app/projects/${project.id}/board`} className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">
                <KanbanSquare className="size-4" />
                Open board
              </Link>
              <Button variant="secondary" type="button">
                <ExternalLink className="size-4" />
                Repository
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-5">
          <CalendarDays className="size-5 text-primary" />
          <p className="mt-4 text-sm font-semibold text-foreground/55">Deadline</p>
          <p className="mt-1 font-display text-2xl font-bold tracking-normal">
            {new Date(project.dueDate).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          </p>
        </Card>
        <Card className="p-5">
          <GitBranch className="size-5 text-success" />
          <p className="mt-4 text-sm font-semibold text-foreground/55">Repository</p>
          <p className="mt-1 truncate font-display text-2xl font-bold tracking-normal">{project.repository}</p>
        </Card>
        <Card className="p-5">
          <UsersRound className="size-5 text-warning" />
          <p className="mt-4 text-sm font-semibold text-foreground/55">Members</p>
          <p className="mt-1 font-display text-2xl font-bold tracking-normal">{project.members.length}</p>
        </Card>
        <Card className="p-5">
          <Bot className="size-5 text-accent" />
          <p className="mt-4 text-sm font-semibold text-foreground/55">AI risk</p>
          <p className="mt-1 font-display text-2xl font-bold tracking-normal">{project.aiRiskScore}%</p>
        </Card>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <div className="space-y-5">
          <Card className="p-5">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Sprint Goal</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-foreground/62">{project.sprintGoal}</p>
              </div>
              <div className="sm:min-w-48">
                <div className="h-2 rounded-full bg-muted">
                  <div className="h-2 rounded-full bg-primary" style={{ width: `${project.progress}%` }} />
                </div>
                <p className="mt-2 text-right text-xs font-bold text-foreground/52">{project.progress}% complete</p>
              </div>
            </div>
          </Card>
          <ProjectTaskPreviewTable tasks={project.tasks} />
          <ProjectCommitFeed commits={project.commits} />
        </div>

        <aside className="space-y-5">
          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Health Summary</h2>
            <p className="mt-2 text-sm leading-6 text-foreground/62">{project.healthSummary}</p>
            <div className="mt-5 flex -space-x-2">
              {project.members.map((member) => (
                <div key={member.id} className="flex size-9 items-center justify-center rounded-full border-2 border-card bg-primary text-xs font-black text-white">
                  {member.initials}
                </div>
              ))}
            </div>
          </Card>
          <ProjectMilestoneRail milestones={project.milestones} />
          <ProjectAiNotes notes={project.aiNotes} />
        </aside>
      </section>
    </main>
  );
}