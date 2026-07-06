export const dashboardKeys = {
  all: ["dashboard"] as const,
  summary: (workspaceId: string) => [...dashboardKeys.all, "summary", workspaceId] as const,
};