import { useQuery } from "@tanstack/react-query";

import { projectsKeys } from "../api/projects.keys";
import { projectsService } from "../api/projects.service";

export function useProject(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: projectsKeys.detail(workspaceId, projectId),
    queryFn: () => projectsService.getProject(workspaceId, projectId),
  });
}