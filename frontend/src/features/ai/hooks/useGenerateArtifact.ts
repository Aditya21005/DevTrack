import { useMutation, useQueryClient } from "@tanstack/react-query";

import { aiKeys } from "../api/ai.keys";
import { aiService } from "../api/ai.service";
import type { AiActivityItem, AiPromptInput } from "../types";

export function useGenerateArtifact(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AiPromptInput) => aiService.generateArtifact(workspaceId, input),
    onSuccess: (artifact) => {
      queryClient.setQueryData<AiActivityItem[]>(aiKeys.history(workspaceId), (current = []) => [
        { id: artifact.id, mode: artifact.mode, title: artifact.title, createdAt: artifact.createdAt, accepted: false },
        ...current.filter((item) => item.id !== artifact.id),
      ]);
    },
  });
}