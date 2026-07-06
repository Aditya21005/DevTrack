import { AlertTriangle, CalendarDays, CheckCircle2, GitBranch, PauseCircle, PlayCircle, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { ProjectSummary } from "../types";

const statusMeta = {
  planned: { label: "Planned", icon: PauseCircle, className: "bg-muted text-foreground/70" },
  active: { label: "Active", icon: PlayCircle, className: "bg-primary/10 text-primary" },
  on_hold: { label: "On hold", icon: PauseCircle, className: "bg-accent/10 text-accent" },
  completed: { label: "Completed", icon: CheckCircle2, className: "bg-success/10 text-success" },
  at_risk: { label: "At risk", icon: AlertTriangle, className: "bg-warning/10 text-warning" },
};

const priorityClass = {
  low: "text-foreground/45",
  medium: "text-primary",
  high: "text-warning",
  urgent: "text-accent",
};

interface ProjectCardProps {
  project: ProjectSummary;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const meta = statusMeta[project.status];
  const StatusIcon = meta.icon;

  return (
    <Card className="group overflow-hidden p-5 transition hover:-translate-y-0.5 hover:border-primary/35">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-muted px-2 py-1 text-xs font-bold text-foreground/70">{project.key}</span>
            <span className={cn("inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-bold", meta.className)}>
              <StatusIcon className="size-3.5" />
              {meta.label}
            </span>
          </div>
          <h2 className="mt-4 truncate font-display text-xl font-bold tracking-normal">{project.name}</h2>
          <p className="mt-2 line-clamp-2 min-h-12 text-sm leading-6 text-foreground/60">{project.description}</p>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center rounded-md bg-background text-sm font-black text-primary ring-1 ring-border">
          {project.owner.initials}
        </div>
      </div>

      <div className="mt-5 h-2 rounded-full bg-muted">
        <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${project.progress}%` }} />
      </div>
      <div className="mt-2 flex items-center justify-between text-xs font-semibold text-foreground/52">
        <span>{project.progress}% complete</span>
        <span>{project.completedTasks} done / {project.openTasks} open</span>
      </div>

      <div className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
        <div className="rounded-md border border-border bg-background p-3">
          <CalendarDays className="size-4 text-primary" />
          <p className="mt-2 text-xs font-semibold text-foreground/50">Deadline</p>
          <p className="font-bold">{new Date(project.dueDate).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</p>
        </div>
        <div className="rounded-md border border-border bg-background p-3">
          <GitBranch className="size-4 text-success" />
          <p className="mt-2 text-xs font-semibold text-foreground/50">Repository</p>
          <p className="truncate font-bold">{project.repository}</p>
        </div>
        <div className="rounded-md border border-border bg-background p-3">
          <Sparkles className="size-4 text-accent" />
          <p className="mt-2 text-xs font-semibold text-foreground/50">AI risk</p>
          <p className="font-bold">{project.aiRiskScore}%</p>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-3 border-t border-border pt-4">
        <p className={cn("text-sm font-bold capitalize", priorityClass[project.priority])}>{project.priority} priority</p>
        <Link to={`/app/projects/${project.id}`} className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-muted px-4 text-sm font-semibold text-foreground transition hover:bg-muted/80 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">Open detail</Link>
      </div>
    </Card>
  );
}