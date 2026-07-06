import { GripVertical, MessageSquare, Paperclip, UserRound } from "lucide-react";

import { cn } from "@/lib/cn";
import type { KanbanTask } from "../types";

const priorityClass = {
  low: "text-foreground/45 bg-muted",
  medium: "text-primary bg-primary/10",
  high: "text-warning bg-warning/10",
  urgent: "text-accent bg-accent/10",
};

interface KanbanTaskCardProps {
  task: KanbanTask;
  onDragStart: (taskId: string) => void;
}

export function KanbanTaskCard({ task, onDragStart }: KanbanTaskCardProps) {
  return (
    <article
      className="group cursor-grab rounded-lg border border-border bg-card p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/35 active:cursor-grabbing"
      draggable
      onDragStart={(event) => {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", task.id);
        onDragStart(task.id);
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <span className="rounded bg-muted px-2 py-1 text-xs font-black text-foreground/62">{task.key}</span>
          <h3 className="mt-3 text-sm font-bold leading-5">{task.title}</h3>
        </div>
        <GripVertical className="size-4 shrink-0 text-foreground/30 transition group-hover:text-primary" />
      </div>
      <p className="mt-2 line-clamp-2 text-xs leading-5 text-foreground/55">{task.description}</p>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {task.labels.map((label) => (
          <span key={label} className="rounded bg-background px-2 py-1 text-[11px] font-bold text-foreground/55 ring-1 ring-border">
            {label}
          </span>
        ))}
      </div>

      <div className="mt-4 h-1.5 rounded-full bg-muted">
        <div className="h-1.5 rounded-full bg-primary" style={{ width: `${task.progress}%` }} />
      </div>

      <div className="mt-4 flex items-center justify-between gap-3 text-xs font-semibold text-foreground/52">
        <span className={cn("rounded px-2 py-1 capitalize", priorityClass[task.priority])}>{task.priority}</span>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1"><MessageSquare className="size-3.5" />{task.comments}</span>
          <span className="inline-flex items-center gap-1"><Paperclip className="size-3.5" />{task.attachments}</span>
          <span className="inline-flex items-center gap-1"><UserRound className="size-3.5" />{task.assignee.initials}</span>
        </div>
      </div>
    </article>
  );
}