from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .gemini_service import GeminiResponse, GeminiService, get_gemini_service


class SprintPlannerInputError(ValueError):
    """Raised when sprint planning input is invalid."""


@dataclass(frozen=True)
class SprintCandidateTask:
    id: str
    title: str
    priority: str = "medium"
    estimate: float | None = None
    status: str | None = None
    assignee: str | None = None
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "estimate": self.estimate,
            "status": self.status,
            "assignee": self.assignee,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SprintPlanningRequest:
    sprint_name: str
    goals: list[str]
    candidate_tasks: list[SprintCandidateTask]
    capacity_notes: str | None = None
    team_notes: str | None = None
    planning_constraints: list[str] = field(default_factory=list)


class SprintPlannerService:
    """AI workflow for selecting and sequencing sprint work."""

    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service

    def generate(self, request: SprintPlanningRequest) -> GeminiResponse:
        self._validate(request)
        capacity_notes = self._build_capacity_notes(request)
        return self._gemini().plan_sprint(
            sprint_name=request.sprint_name.strip(),
            goals=[goal.strip() for goal in request.goals if goal.strip()],
            candidate_tasks=[task.to_prompt_dict() for task in request.candidate_tasks],
            capacity_notes=capacity_notes,
        )

    def _build_capacity_notes(self, request: SprintPlanningRequest) -> str:
        parts = [
            request.capacity_notes or "No explicit capacity notes provided",
            "Team notes: " + (request.team_notes or "None"),
            "Planning constraints:",
            self._format_list(request.planning_constraints),
            "Output format: recommend scope, sequence tasks, identify risks, defer items, and state assumptions.",
        ]
        return "\n".join(parts)

    def _validate(self, request: SprintPlanningRequest) -> None:
        if not request.sprint_name.strip():
            raise SprintPlannerInputError("sprint_name is required")
        if not [goal for goal in request.goals if goal.strip()]:
            raise SprintPlannerInputError("At least one sprint goal is required")
        if not request.candidate_tasks:
            raise SprintPlannerInputError("At least one candidate task is required")
        if len(request.candidate_tasks) > 200:
            raise SprintPlannerInputError("candidate_tasks must contain at most 200 items")
        for task in request.candidate_tasks:
            if not task.id.strip() or not task.title.strip():
                raise SprintPlannerInputError("Each candidate task requires id and title")
            if task.estimate is not None and task.estimate < 0:
                raise SprintPlannerInputError("Task estimates cannot be negative")

    def _gemini(self) -> GeminiService:
        if self._gemini_service is None:
            self._gemini_service = get_gemini_service()
        return self._gemini_service

    def _format_list(self, values: list[str]) -> str:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            return "None"
        return "\n".join(f"- {value}" for value in cleaned)


def get_sprint_planner_service() -> SprintPlannerService:
    return SprintPlannerService()
