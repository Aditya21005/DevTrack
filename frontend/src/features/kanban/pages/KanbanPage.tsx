import { AlertTriangle, ArrowLeft, Clock3, KanbanSquare, RadioTower, RefreshCcw, Route } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { KanbanBoard } from "../components/KanbanBoard";
import { useKanbanBoard } from "../hooks/useKanbanBoard";
import { useMoveTask } from "../hooks/useMoveTask";

export default function KanbanPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId ?? "project_core_api";
  const boardQuery = useKanbanBoard(projectId);
  const moveTask = useMoveTask(projectId);

  if (boardQuery.isLoading) {
    return (
      <main className="space-y-6 p-5 sm:p-6 lg:p-8">
        <div className="h-44 animate-pulse rounded-lg bg-muted" />
        <div className="flex gap-4 overflow-hidden">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-[640px] w-80 shrink-0 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </main>
    );
  }

  if (boardQuery.isError || !boardQuery.data) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center p-6">
        <Card className="max-w-md p-6 text-center">
          <AlertTriangle className="mx-auto size-10 text-warning" />
          <h1 className="mt-4 font-display text-2xl font-bold tracking-normal">Board unavailable</h1>
          <p className="mt-2 text-sm leading-6 text-foreground/60">The kanban board could not be loaded.</p>
          <Button className="mt-5" onClick={() => boardQuery.refetch()}>
            <RefreshCcw className="size-4" />
            Retry
          </Button>
        </Card>
      </main>
    );
  }

  const board = boardQuery.data;
  const totalTasks = board.columns.reduce((sum, column) => sum + column.tasks.length, 0);
  const doneTasks = board.columns.find((column) => column.category === "done")?.tasks.length ?? 0;

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-7 top-0 hidden w-16 branch-rail opacity-20 lg:block" aria-hidden="true" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Link className="inline-flex items-center gap-2 text-sm font-bold text-foreground/58 transition hover:text-primary" to={`/app/projects/${projectId}`}>
              <ArrowLeft className="size-4" />
              Back to project
            </Link>
            <div className="mt-5 inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-bold text-primary">
              <KanbanSquare className="size-4" />
              {board.projectKey} board
            </div>
            <h1 className="mt-5 max-w-4xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">
              {board.projectName}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-foreground/62 sm:text-base">
              Drag cards between lanes to update status and ordering. The UI applies the move optimistically, then reconciles with the service response.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 lg:min-w-[390px]">
            <div className="rounded-lg border border-border bg-background p-3">
              <Route className="size-4 text-primary" />
              <p className="mt-2 text-2xl font-bold">{totalTasks}</p>
              <p className="text-xs font-semibold text-foreground/50">Tasks</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <RadioTower className="size-4 text-success" />
              <p className="mt-2 text-2xl font-bold">{doneTasks}</p>
              <p className="text-xs font-semibold text-foreground/50">Done</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <Clock3 className="size-4 text-warning" />
              <p className="mt-2 text-sm font-bold">{board.updatedAt}</p>
              <p className="text-xs font-semibold text-foreground/50">Updated</p>
            </div>
          </div>
        </div>
      </section>

      {moveTask.isError ? (
        <Card className="border-warning/40 bg-warning/10 p-4 text-sm font-semibold text-warning">
          Move failed. The board has been restored to the last confirmed state.
        </Card>
      ) : null}

      <KanbanBoard
        board={board}
        onMoveTask={(taskId, toColumnId, toIndex) => {
          moveTask.mutate({ projectId, taskId, toColumnId, toIndex });
        }}
      />
    </main>
  );
}