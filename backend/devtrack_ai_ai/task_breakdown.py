from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .gemini_service import GeminiResponse, GeminiService, get_gemini_service


class TaskBreakdownInputError(ValueError):
    """Raised when task breakdown input is invalid."""


@dataclass(frozen=True)
class TaskBreakdownRequest:
    title: str
    description: str | None = None
    project_context: str | None = None
    acceptance_hints: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    technical_context: dict[str, Any] = field(default_factory=dict)


class TaskBreakdownService:
    """AI workflow for converting a high-level task into executable subtasks."""

    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service

    def generate(self, request: TaskBreakdownRequest) -> GeminiResponse:
        self._validate(request)
        context = self._build_context(request)
        return self._gemini().breakdown_task(
            title=request.title.strip(),
            description=request.description,
            context=context,
        )

    def _build_context(self, request: TaskBreakdownRequest) -> str:
        return "\n".join(
            [
                "Project context:",
                request.project_context or "Not provided",
                "",
                "Acceptance hints:",
                self._format_list(request.acceptance_hints),
                "",
                "Constraints:",
                self._format_list(request.constraints),
                "",
                "Known dependencies:",
                self._format_list(request.dependencies),
                "",
                "Technical context:",
                self._format_mapping(request.technical_context),
                "",
                "Output format:",
                "Return Markdown with sections: Summary, Subtasks, Acceptance Criteria, Risks, Implementation Order.",
                "Keep subtasks small enough to be assigned independently.",
            ]
        )

    def _validate(self, request: TaskBreakdownRequest) -> None:
        if not request.title.strip():
            raise TaskBreakdownInputError("Task title is required")
        if len(request.title) > 300:
            raise TaskBreakdownInputError("Task title must be at most 300 characters")
        for field_name, values in {
            "acceptance_hints": request.acceptance_hints,
            "constraints": request.constraints,
            "dependencies": request.dependencies,
        }.items():
            if len(values) > 50:
                raise TaskBreakdownInputError(f"{field_name} must contain at most 50 items")

    def _gemini(self) -> GeminiService:
        if self._gemini_service is None:
            self._gemini_service = get_gemini_service()
        return self._gemini_service

    def _format_list(self, values: list[str]) -> str:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            return "None"
        return "\n".join(f"- {value}" for value in cleaned)

    def _format_mapping(self, values: dict[str, Any]) -> str:
        if not values:
            return "None"
        return "\n".join(f"- {key}: {value}" for key, value in values.items())


def get_task_breakdown_service() -> TaskBreakdownService:
    return TaskBreakdownService()
