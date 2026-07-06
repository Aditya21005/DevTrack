import { useQuery } from "@tanstack/react-query";

import { projectsKeys } from "../api/projects.keys";
import { projectsService } from "../api/projects.service";
import type { ProjectFilters } from "../types";

export function useProjects(workspaceId: string, filters: ProjectFilters) {
  return useQuery({
    queryKey: projectsKeys.list(workspaceId, filters),
    queryFn: () => projectsService.listProjects(workspaceId, filters),
  });
}