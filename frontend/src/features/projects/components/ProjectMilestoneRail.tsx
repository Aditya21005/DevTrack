import { CheckCircle2, Circle, CircleDashed, OctagonAlert } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { ProjectMilestone } from "../types";

const milestoneMeta = {
  complete: { icon: CheckCircle2, className: "text-success bg-success/10", dot: "bg-success" },
  active: { icon: CircleDashed, className: "text-primary bg-primary/10", dot: "bg-primary" },
  blocked: { icon: OctagonAlert, className: "text-warning bg-warning/10", dot: "bg-warning" },
  upcoming: { icon: Circle, className: "text-foreground/50 bg-muted", dot: "bg-border" },
};

interface ProjectMilestoneRailProps {
  milestones: ProjectMilestone[];
}

export function ProjectMilestoneRail({ milestones }: ProjectMilestoneRailProps) {
  return (
    <Card className="p-5">
      <h2 className="font-display text-xl font-bold tracking-normal">Milestone Rail</h2>
      <p className="mt-1 text-sm text-foreground/58">The project path from scope to release.</p>
      <div className="relative mt-6 space-y-5 pl-8 before:absolute before:bottom-3 before:left-3 before:top-3 before:w-px before:bg-border">
        {milestones.map((milestone) => {
          const meta = milestoneMeta[milestone.status];
          const Icon = meta.icon;
          return (
            <article key={milestone.id} className="relative">
              <span className={cn("absolute -left-[26px] top-2 size-3 rounded-full ring-4 ring-card", meta.dot)} />
              <div className="flex items-start justify-between gap-4 rounded-lg border border-border bg-background p-4">
                <div className="min-w-0">
                  <div className={cn("inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-bold capitalize", meta.className)}>
                    <Icon className="size-3.5" />
                    {milestone.status}
                  </div>
                  <h3 className="mt-3 text-sm font-bold">{milestone.title}</h3>
                </div>
                <time className="shrink-0 text-xs font-semibold text-foreground/50">
                  {new Date(milestone.dueDate).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </time>
              </div>
            </article>
          );
        })}
      </div>
    </Card>
  );
}