import { AlertTriangle, CheckCircle2, CircleDashed } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { ProjectHealth } from "../types";

const statusMeta = {
  "on-track": { label: "On track", icon: CheckCircle2, className: "text-success bg-success/10" },
  "at-risk": { label: "At risk", icon: AlertTriangle, className: "text-warning bg-warning/10" },
  blocked: { label: "Blocked", icon: CircleDashed, className: "text-accent bg-accent/10" },
};

interface ProjectHealthListProps {
  projects: ProjectHealth[];
}

export function ProjectHealthList({ projects }: ProjectHealthListProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">Project Health</h2>
          <p className="mt-1 text-sm text-foreground/58">Delivery risk across active workstreams.</p>
        </div>
      </div>

      <div className="mt-5 space-y-4">
        {projects.map((project) => {
          const meta = statusMeta[project.status];
          const Icon = meta.icon;

          return (
            <article key={project.id} className="rounded-lg border border-border bg-background p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-muted px-2 py-1 text-xs font-bold text-foreground/70">{project.key}</span>
                    <span className={cn("inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-bold", meta.className)}>
                      <Icon className="size-3.5" />
                      {meta.label}
                    </span>
                  </div>
                  <h3 className="mt-3 text-sm font-bold">{project.name}</h3>
                </div>
                <div className="text-right text-sm">
                  <p className="font-semibold">{project.openTasks} open</p>
                  <p className="text-foreground/52">{project.dueLabel}</p>
                </div>
              </div>
              <div className="mt-4 h-2 rounded-full bg-muted">
                <div className="h-2 rounded-full bg-primary" style={{ width: `${project.progress}%` }} />
              </div>
            </article>
          );
        })}
      </div>
    </Card>
  );
}