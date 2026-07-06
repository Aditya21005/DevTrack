export const settingsKeys = {
  all: ["settings"] as const,
  summary: (workspaceId: string) => [...settingsKeys.all, "summary", workspaceId] as const,
};