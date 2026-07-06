export const aiKeys = {
  all: ["ai"] as const,
  history: (workspaceId: string) => [...aiKeys.all, "history", workspaceId] as const,
};