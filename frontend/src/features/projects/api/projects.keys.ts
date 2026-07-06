import type { ProjectFilters } from "../types";

export const projectsKeys = {
  all: ["projects"] as const,
  lists: () => [...projectsKeys.all, "list"] as const,
  list: (workspaceId: string, filters: ProjectFilters) => [...projectsKeys.lists(), workspaceId, filters] as const,
  details: () => [...projectsKeys.all, "detail"] as const,
  detail: (workspaceId: string, projectId: string) => [...projectsKeys.details(), workspaceId, projectId] as const,
};