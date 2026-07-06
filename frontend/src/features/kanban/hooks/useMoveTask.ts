import { useMutation, useQueryClient } from "@tanstack/react-query";

import { kanbanKeys } from "../api/kanban.keys";
import { kanbanService, moveTaskOnBoard } from "../api/kanban.service";
import type { KanbanBoard, MoveTaskInput } from "../types";

export function useMoveTask(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: MoveTaskInput) => kanbanService.moveTask(input),
    onMutate: async (input) => {
      const queryKey = kanbanKeys.board(projectId);
      await queryClient.cancelQueries({ queryKey });
      const previousBoard = queryClient.getQueryData<KanbanBoard>(queryKey);

      if (previousBoard) {
        queryClient.setQueryData<KanbanBoard>(queryKey, moveTaskOnBoard(previousBoard, input));
      }

      return { previousBoard };
    },
    onError: (_error, _input, context) => {
      if (context?.previousBoard) {
        queryClient.setQueryData(kanbanKeys.board(projectId), context.previousBoard);
      }
    },
    onSuccess: (board) => {
      queryClient.setQueryData(kanbanKeys.board(projectId), board);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: kanbanKeys.board(projectId) });
    },
  });
}