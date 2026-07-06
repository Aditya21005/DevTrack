from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .gemini_service import GeminiResponse, GeminiService, get_gemini_service


class DailySummaryInputError(ValueError):
    """Raised when daily summary input is invalid."""


@dataclass(frozen=True)
class DailySummaryRequest:
    summary_date: date | str
    completed: list[str] = field(default_factory=list)
    in_progress: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    meetings: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    audience: str = "engineering team"


class DailySummaryService:
    """AI workflow for turning activity into a clear daily engineering summary."""

    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service

    def generate(self, request: DailySummaryRequest) -> GeminiResponse:
        self._validate(request)
        completed = self._augment_completed(request)
        in_progress = self._augment_in_progress(request)
        blockers = self._augment_blockers(request)
        return self._gemini().daily_summary(
            summary_date=request.summary_date,
            completed=completed,
            in_progress=in_progress,
            blockers=blockers,
        )

    def _augment_completed(self, request: DailySummaryRequest) -> list[str]:
        values = [*request.completed]
        if request.meetings:
            values.append("Meetings attended: " + "; ".join(item.strip() for item in request.meetings if item.strip()))
        return values

    def _augment_in_progress(self, request: DailySummaryRequest) -> list[str]:
        values = [*request.in_progress]
        values.append(f"Audience: {request.audience.strip()}")
        values.append("Output format: concise standup summary with sections for Completed, In Progress, Blockers, Risks, Next Steps.")
        return values

    def _augment_blockers(self, request: DailySummaryRequest) -> list[str]:
        values = [*request.blockers]
        if request.risks:
            values.append("Risks: " + "; ".join(item.strip() for item in request.risks if item.strip()))
        return values

    def _validate(self, request: DailySummaryRequest) -> None:
        if not str(request.summary_date).strip():
            raise DailySummaryInputError("summary_date is required")
        if not request.completed and not request.in_progress and not request.blockers:
            raise DailySummaryInputError("At least one completed, in_progress, or blocker item is required")
        if not request.audience.strip():
            raise DailySummaryInputError("audience is required")

    def _gemini(self) -> GeminiService:
        if self._gemini_service is None:
            self._gemini_service = get_gemini_service()
        return self._gemini_service


def get_daily_summary_service() -> DailySummaryService:
    return DailySummaryService()
