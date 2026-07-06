import { useQuery } from "@tanstack/react-query";

import { githubKeys } from "../api/github.keys";
import { githubService } from "../api/github.service";

export function useGithubSummary(workspaceId: string) {
  return useQuery({
    queryKey: githubKeys.summary(workspaceId),
    queryFn: () => githubService.getSummary(workspaceId),
  });
}