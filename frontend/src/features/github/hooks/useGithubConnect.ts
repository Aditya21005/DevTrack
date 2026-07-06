import { useMutation, useQueryClient } from "@tanstack/react-query";

import { githubKeys } from "../api/github.keys";
import { githubService } from "../api/github.service";

export function useGithubConnect(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => githubService.connect(workspaceId),
    onSuccess: (summary) => {
      queryClient.setQueryData(githubKeys.summary(workspaceId), summary);
    },
  });
}