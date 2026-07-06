import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { KanbanBoard, KanbanColumn, MoveTaskInput } from "../types";


const people = {
  avery: { id: "u1", name: "Avery Chen", initials: "AC" },
  mira: { id: "u2", name: "Mira Patel", initials: "MP" },
  noah: { id: "u3", name: "Noah Kim", initials: "NK" },
  sam: { id: "u4", name: "Sam Rivera", initials: "SR" },
};

let mockBoards: Record<string, KanbanBoard> = {
  project_core_api: {
    id: "board_core_api",
    projectId: "project_core_api",
    projectKey: "CORE",
    projectName: "Core API Reliability",
    updatedAt: "4 minutes ago",
    columns: [
      {
        id: "todo",
        title: "Todo",
        category: "todo",
        wipLimit: 8,
        tasks: [
          {
            id: "task_core_122",
            key: "CORE-122",
            title: "Document session rollback behavior",
            description: "Capture transaction boundaries and operational failure modes.",
            priority: "medium",
            labels: ["docs", "backend"],
            assignee: people.sam,
            progress: 18,
            comments: 2,
            attachments: 1,
          },
          {
            id: "task_core_125",
            key: "CORE-125",
            title: "Add dashboard query fixtures",
            description: "Prepare optimized analytics fixtures for acceptance checks.",
            priority: "low",
            labels: ["analytics"],
            assignee: people.noah,
            progress: 5,
            comments: 1,
            attachments: 0,
          },
        ],
      },
      {
        id: "in_progress",
        title: "In Progress",
        category: "in_progress",
        wipLimit: 5,
        tasks: [
          {
            id: "task_core_118",
            key: "CORE-118",
            title: "Validate service-layer contract",
            description: "Check auth, workspace, and project services against route expectations.",
            priority: "high",
            labels: ["backend", "contract"],
            assignee: people.avery,
            progress: 64,
            comments: 5,
            attachments: 2,
          },
          {
            id: "task_core_123",
            key: "CORE-123",
            title: "Tighten database exception mapping",
            description: "Make infrastructure errors stable for route handlers and workers.",
            priority: "urgent",
            labels: ["database"],
            assignee: people.mira,
            progress: 71,
            comments: 3,
            attachments: 0,
          },
        ],
      },
      {
        id: "review",
        title: "Review",
        category: "review",
        wipLimit: 4,
        tasks: [
          {
            id: "task_core_119",
            key: "CORE-119",
            title: "Add UI acceptance states",
            description: "Cover empty, loading, failure, and optimistic update paths.",
            priority: "urgent",
            labels: ["frontend", "qa"],
            assignee: people.mira,
            progress: 86,
            comments: 7,
            attachments: 3,
          },
        ],
      },
      {
        id: "done",
        title: "Done",
        category: "done",
        tasks: [
          {
            id: "task_core_121",
            key: "CORE-121",
            title: "Close analytics instrumentation",
            description: "Emit project and dashboard telemetry from the app shell.",
            priority: "low",
            labels: ["telemetry"],
            assignee: people.noah,
            progress: 100,
            comments: 4,
            attachments: 1,
          },
        ],
      },
    ],
  },
};

function cloneBoard(board: KanbanBoard): KanbanBoard {
  return {
    ...board,
    columns: board.columns.map((column) => ({ ...column, tasks: column.tasks.map((task) => ({ ...task, labels: [...task.labels] })) })),
  };
}

function fallbackBoard(projectId: string): KanbanBoard {
  const base = cloneBoard(mockBoards.project_core_api);
  return {
    ...base,
    id: `board_${projectId}`,
    projectId,
    projectKey: projectId.includes("kanban") || projectId === "demo" ? "KAN" : base.projectKey,
    projectName: projectId.includes("kanban") || projectId === "demo" ? "Realtime Kanban Moves" : base.projectName,
  };
}

export function moveTaskOnBoard(board: KanbanBoard, input: MoveTaskInput): KanbanBoard {
  const next = cloneBoard(board);
  let movingTask = null;

  for (const column of next.columns) {
    const taskIndex = column.tasks.findIndex((task) => task.id === input.taskId);
    if (taskIndex >= 0) {
      movingTask = column.tasks.splice(taskIndex, 1)[0];
      break;
    }
  }

  if (!movingTask) {
    return next;
  }

  const destination = next.columns.find((column) => column.id === input.toColumnId) ?? next.columns[0];
  const boundedIndex = Math.max(0, Math.min(input.toIndex, destination.tasks.length));
  destination.tasks.splice(boundedIndex, 0, movingTask);
  next.updatedAt = "just now";
  return next;
}

export const kanbanService = {
  async getBoard(projectId: string): Promise<KanbanBoard> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(280);
      const board = mockBoards[projectId] ?? fallbackBoard(projectId);
      mockBoards = { ...mockBoards, [projectId]: board };
      return cloneBoard(board);
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<KanbanBoard>(`/projects/${projectId}/kanban`);
    return response.data;
  },

  async moveTask(input: MoveTaskInput): Promise<KanbanBoard> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(260);
      const board = mockBoards[input.projectId] ?? fallbackBoard(input.projectId);
      const moved = moveTaskOnBoard(board, input);
      mockBoards = { ...mockBoards, [input.projectId]: moved };
      return cloneBoard(moved);
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.patch<KanbanBoard>(`/projects/${input.projectId}/kanban/tasks/${input.taskId}/move`, input);
    return response.data;
  },
};


