import { useQuery } from "@tanstack/react-query";

import { kanbanKeys } from "../api/kanban.keys";
import { kanbanService } from "../api/kanban.service";

export function useKanbanBoard(projectId: string) {
  return useQuery({
    queryKey: kanbanKeys.board(projectId),
    queryFn: () => kanbanService.getBoard(projectId),
  });
}