export const kanbanKeys = {
  all: ["kanban"] as const,
  boards: () => [...kanbanKeys.all, "board"] as const,
  board: (projectId: string) => [...kanbanKeys.boards(), projectId] as const,
};