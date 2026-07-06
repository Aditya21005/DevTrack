import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import type { KanbanColumn as KanbanColumnType } from "../types";
import { KanbanTaskCard } from "./KanbanTaskCard";

const categoryClass = {
  todo: "border-foreground/20",
  in_progress: "border-primary/45",
  review: "border-warning/45",
  done: "border-success/45",
};

interface KanbanColumnProps {
  column: KanbanColumnType;
  activeTaskId: string | null;
  onDragStart: (taskId: string) => void;
  onDropTask: (columnId: string, toIndex: number, taskId: string) => void;
}

export function KanbanColumn({ column, activeTaskId, onDragStart, onDropTask }: KanbanColumnProps) {
  const isOverLimit = column.wipLimit !== undefined && column.tasks.length > column.wipLimit;

  return (
    <section
      className={cn("flex min-h-[640px] w-[320px] shrink-0 flex-col rounded-lg border-t-4 bg-background", categoryClass[column.category])}
      onDragOver={(event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
      }}
      onDrop={(event) => {
        event.preventDefault();
        const taskId = event.dataTransfer.getData("text/plain") || activeTaskId;
        if (taskId) {
          onDropTask(column.id, column.tasks.length, taskId);
        }
      }}
    >
      <header className="border-b border-border p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-lg font-bold tracking-normal">{column.title}</h2>
            <p className="mt-1 text-xs font-semibold text-foreground/48">
              {column.tasks.length} tasks{column.wipLimit ? ` / WIP ${column.wipLimit}` : ""}
            </p>
          </div>
          <Button variant="ghost" className="size-9 px-0" type="button" aria-label={`Add task to ${column.title}`}>
            <Plus className="size-4" />
          </Button>
        </div>
        {isOverLimit ? <p className="mt-3 rounded bg-warning/10 px-2 py-1 text-xs font-bold text-warning">WIP limit exceeded</p> : null}
      </header>

      <div className="flex-1 space-y-3 p-3">
        {column.tasks.map((task, index) => (
          <div
            key={task.id}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              event.stopPropagation();
              const taskId = event.dataTransfer.getData("text/plain") || activeTaskId;
              if (taskId) {
                onDropTask(column.id, index, taskId);
              }
            }}
          >
            <KanbanTaskCard task={task} onDragStart={onDragStart} />
          </div>
        ))}

        {column.tasks.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-5 text-center text-sm font-semibold text-foreground/42">
            Drop tasks here
          </div>
        ) : null}
      </div>
    </section>
  );
}