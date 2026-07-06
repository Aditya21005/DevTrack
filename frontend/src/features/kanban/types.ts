export type KanbanTaskPriority = "low" | "medium" | "high" | "urgent";

export interface KanbanAssignee {
  id: string;
  name: string;
  initials: string;
}

export interface KanbanTask {
  id: string;
  key: string;
  title: string;
  description: string;
  priority: KanbanTaskPriority;
  labels: string[];
  assignee: KanbanAssignee;
  progress: number;
  comments: number;
  attachments: number;
}

export interface KanbanColumn {
  id: string;
  title: string;
  category: "todo" | "in_progress" | "review" | "done";
  wipLimit?: number;
  tasks: KanbanTask[];
}

export interface KanbanBoard {
  id: string;
  projectId: string;
  projectKey: string;
  projectName: string;
  updatedAt: string;
  columns: KanbanColumn[];
}

export interface MoveTaskInput {
  projectId: string;
  taskId: string;
  toColumnId: string;
  toIndex: number;
}