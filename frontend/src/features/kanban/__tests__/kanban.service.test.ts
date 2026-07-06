import { describe, expect, it } from "vitest";

import { moveTaskOnBoard } from "../api/kanban.service";
import type { KanbanBoard } from "../types";

const board: KanbanBoard = {
  id: "board",
  projectId: "project",
  projectKey: "CORE",
  projectName: "Core API Reliability",
  updatedAt: "before",
  columns: [
    {
      id: "todo",
      title: "Todo",
      category: "todo",
      tasks: [
        { id: "task-1", key: "CORE-1", title: "One", description: "First", priority: "medium", labels: [], assignee: { id: "u1", name: "Avery", initials: "AC" }, progress: 0, comments: 0, attachments: 0 },
      ],
    },
    {
      id: "done",
      title: "Done",
      category: "done",
      tasks: [],
    },
  ],
};

describe("moveTaskOnBoard", () => {
  it("moves a task to the destination column without mutating the original board", () => {
    const moved = moveTaskOnBoard(board, { projectId: "project", taskId: "task-1", toColumnId: "done", toIndex: 0 });

    expect(board.columns[0].tasks).toHaveLength(1);
    expect(moved.columns[0].tasks).toHaveLength(0);
    expect(moved.columns[1].tasks[0].id).toBe("task-1");
    expect(moved.updatedAt).toBe("just now");
  });
});