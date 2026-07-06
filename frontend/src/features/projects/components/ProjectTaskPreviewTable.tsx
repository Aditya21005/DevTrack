import { CircleDot, Flag, UserRound } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { ProjectTaskPreview } from "../types";

const statusClass = {
  todo: "bg-muted text-foreground/60",
  in_progress: "bg-primary/10 text-primary",
  review: "bg-warning/10 text-warning",
  done: "bg-success/10 text-success",
};

const priorityClass = {
  low: "text-foreground/45",
  medium: "text-primary",
  high: "text-warning",
  urgent: "text-accent",
};

interface ProjectTaskPreviewTableProps {
  tasks: ProjectTaskPreview[];
}

export function ProjectTaskPreviewTable({ tasks }: ProjectTaskPreviewTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border p-5">
        <h2 className="font-display text-xl font-bold tracking-normal">Task Preview</h2>
        <p className="mt-1 text-sm text-foreground/58">High-signal work items from this project.</p>
      </div>
      <div className="divide-y divide-border">
        {tasks.map((task) => (
          <article key={task.id} className="grid gap-3 p-4 sm:grid-cols-[1fr_130px_120px] sm:items-center">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-muted px-2 py-1 text-xs font-black text-foreground/62">{task.key}</span>
                <span className={cn("inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-bold", statusClass[task.status])}>
                  <CircleDot className="size-3" />
                  {task.status.replace("_", " ")}
                </span>
              </div>
              <h3 className="mt-2 text-sm font-bold">{task.title}</h3>
            </div>
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground/62">
              <UserRound className="size-4" />
              {task.assignee.name}
            </div>
            <div className={cn("flex items-center gap-2 text-sm font-bold capitalize", priorityClass[task.priority])}>
              <Flag className="size-4" />
              {task.priority}
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}