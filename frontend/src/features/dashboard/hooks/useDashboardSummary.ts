import { useQuery } from "@tanstack/react-query";

import { dashboardKeys } from "../api/dashboard.keys";
import { dashboardService } from "../api/dashboard.service";

export function useDashboardSummary(workspaceId: string) {
  return useQuery({
    queryKey: dashboardKeys.summary(workspaceId),
    queryFn: () => dashboardService.getSummary(workspaceId),
  });
}