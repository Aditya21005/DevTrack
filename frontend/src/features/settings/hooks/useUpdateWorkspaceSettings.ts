import { useMutation, useQueryClient } from "@tanstack/react-query";

import { settingsKeys } from "../api/settings.keys";
import { settingsService } from "../api/settings.service";
import type { WorkspaceSettingsInput } from "../types";

export function useUpdateWorkspaceSettings(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: WorkspaceSettingsInput) => settingsService.updateWorkspace(workspaceId, input),
    onSuccess: (summary) => {
      queryClient.setQueryData(settingsKeys.summary(workspaceId), summary);
    },
  });
}