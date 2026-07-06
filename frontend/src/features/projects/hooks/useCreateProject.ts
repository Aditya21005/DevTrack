import { useMutation, useQueryClient } from "@tanstack/react-query";

import { projectsKeys } from "../api/projects.keys";
import { projectsService } from "../api/projects.service";
import type { CreateProjectInput } from "../types";

export function useCreateProject(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateProjectInput) => projectsService.createProject(workspaceId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}