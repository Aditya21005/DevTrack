import { useQuery } from "@tanstack/react-query";

import { aiKeys } from "../api/ai.keys";
import { aiService } from "../api/ai.service";

export function useAiHistory(workspaceId: string) {
  return useQuery({
    queryKey: aiKeys.history(workspaceId),
    queryFn: () => aiService.listHistory(workspaceId),
  });
}