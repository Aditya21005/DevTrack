import { useMutation, useQueryClient } from "@tanstack/react-query";

import { settingsKeys } from "../api/settings.keys";
import { settingsService } from "../api/settings.service";
import type { InviteMemberInput } from "../types";

export function useInviteMember(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: InviteMemberInput) => settingsService.inviteMember(workspaceId, input),
    onSuccess: (summary) => {
      queryClient.setQueryData(settingsKeys.summary(workspaceId), summary);
    },
  });
}