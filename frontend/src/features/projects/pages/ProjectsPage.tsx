import { useMemo, useState } from "react";
import { AlertTriangle, FolderKanban, Layers3, Plus, Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";
import { CreateProjectForm } from "../components/CreateProjectForm";
import { ProjectCard } from "../components/ProjectCard";
import { ProjectFilters } from "../components/ProjectFilters";
import { useProjects } from "../hooks/useProjects";
import type { ProjectFilters as ProjectFiltersValue } from "../types";

const workspaceId = "workspace_platform_engineering";

export default function ProjectsPage() {
  const [filters, setFilters] = useState<ProjectFiltersValue>({ search: "", status: "all" });
  const projectsQuery = useProjects(workspaceId, filters);

  const summary = useMemo(() => {
    const projects = projectsQuery.data ?? [];
    return {
      total: projects.length,
      active: projects.filter((project) => project.status === "active").length,
      risk: projects.filter((project) => project.status === "at_risk" || project.status === "on_hold").length,
      avgRisk: projects.length ? Math.round(projects.reduce((sum, project) => sum + project.aiRiskScore, 0) / projects.length) : 0,
    };
  }, [projectsQuery.data]);

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-7 top-0 hidden w-16 branch-rail opacity-20 lg:block" aria-hidden="true" />
        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-bold text-primary">
              <FolderKanban className="size-4" />
              Projects
            </div>
            <h1 className="mt-5 max-w-3xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">
              Track every delivery stream without losing the signal.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-foreground/62 sm:text-base">
              Scan active initiatives, spot risk, and create new project tracks with the same operational model your backend already expects.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 lg:min-w-[360px]">
            <div className="rounded-lg border border-border bg-background p-3">
              <Layers3 className="size-4 text-primary" />
              <p className="mt-2 text-2xl font-bold">{summary.total}</p>
              <p className="text-xs font-semibold text-foreground/50">Visible</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <Plus className="size-4 text-success" />
              <p className="mt-2 text-2xl font-bold">{summary.active}</p>
              <p className="text-xs font-semibold text-foreground/50">Active</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <AlertTriangle className="size-4 text-warning" />
              <p className="mt-2 text-2xl font-bold">{summary.risk}</p>
              <p className="text-xs font-semibold text-foreground/50">Risk</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <div className="space-y-5">
          <Card className="p-4 sm:p-5">
            <ProjectFilters value={filters} onChange={setFilters} />
          </Card>

          {projectsQuery.isLoading ? (
            <div className="grid gap-4 2xl:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-80 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : projectsQuery.isError ? (
            <Card className="p-6 text-center">
              <AlertTriangle className="mx-auto size-10 text-warning" />
              <h2 className="mt-4 font-display text-2xl font-bold tracking-normal">Projects unavailable</h2>
              <p className="mt-2 text-sm text-foreground/60">The workspace project list could not be loaded.</p>
            </Card>
          ) : projectsQuery.data?.length ? (
            <div className="grid gap-4 2xl:grid-cols-2">
              {projectsQuery.data.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <FolderKanban className="mx-auto size-10 text-primary" />
              <h2 className="mt-4 font-display text-2xl font-bold tracking-normal">No projects match this view</h2>
              <p className="mt-2 text-sm text-foreground/60">Adjust the filters or create a new delivery stream.</p>
            </Card>
          )}
        </div>

        <aside className="space-y-5">
          <Card className="p-5">
            <div className="flex items-start gap-3">
              <div className="flex size-10 items-center justify-center rounded-md bg-accent/10 text-accent">
                <Sparkles className="size-5" />
              </div>
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Project Intake</h2>
                <p className="mt-1 text-sm leading-6 text-foreground/58">
                  Create a project shell now. Repository linking, member assignment, and workflow setup come in later screens.
                </p>
              </div>
            </div>
            <div className="mt-5">
              <CreateProjectForm workspaceId={workspaceId} />
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">AI Portfolio Signal</h2>
            <p className="mt-2 text-sm leading-6 text-foreground/60">
              Average risk across this view is <span className="font-bold text-accent">{summary.avgRisk}%</span>. Projects with rising risk should be split before sprint planning.
            </p>
            <div className="mt-4 h-2 rounded-full bg-muted">
              <div className="h-2 rounded-full bg-accent" style={{ width: `${summary.avgRisk}%` }} />
            </div>
          </Card>
        </aside>
      </section>
    </main>
  );
}