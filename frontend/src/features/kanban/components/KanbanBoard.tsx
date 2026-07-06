import { useState } from "react";

import type { KanbanBoard as KanbanBoardType } from "../types";
import { KanbanColumn } from "./KanbanColumn";

interface KanbanBoardProps {
  board: KanbanBoardType;
  onMoveTask: (taskId: string, toColumnId: string, toIndex: number) => void;
}

export function KanbanBoard({ board, onMoveTask }: KanbanBoardProps) {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  return (
    <div className="overflow-x-auto pb-3">
      <div className="flex min-w-max gap-4">
        {board.columns.map((column) => (
          <KanbanColumn
            key={column.id}
            column={column}
            activeTaskId={activeTaskId}
            onDragStart={setActiveTaskId}
            onDropTask={(toColumnId, toIndex, taskId) => {
              onMoveTask(taskId, toColumnId, toIndex);
              setActiveTaskId(null);
            }}
          />
        ))}
      </div>
    </div>
  );
}