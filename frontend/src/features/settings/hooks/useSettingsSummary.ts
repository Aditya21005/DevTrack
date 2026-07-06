import { useQuery } from "@tanstack/react-query";

import { settingsKeys } from "../api/settings.keys";
import { settingsService } from "../api/settings.service";

export function useSettingsSummary(workspaceId: string) {
  return useQuery({
    queryKey: settingsKeys.summary(workspaceId),
    queryFn: () => settingsService.getSummary(workspaceId),
  });
}