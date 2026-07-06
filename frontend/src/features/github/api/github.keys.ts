export const githubKeys = {
  all: ["github"] as const,
  summary: (workspaceId: string) => [...githubKeys.all, "summary", workspaceId] as const,
};