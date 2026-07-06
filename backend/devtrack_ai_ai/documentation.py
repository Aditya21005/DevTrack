from __future__ import annotations

from dataclasses import dataclass, field

from .gemini_service import GeminiResponse, GeminiService, get_gemini_service


class DocumentationInputError(ValueError):
    """Raised when documentation input is invalid."""


@dataclass(frozen=True)
class DocumentationRequest:
    title: str
    source_context: str
    audience: str = "developers"
    doc_type: str = "technical documentation"
    existing_docs: str | None = None
    style_guidelines: list[str] = field(default_factory=list)
    include_sections: list[str] = field(default_factory=list)


class DocumentationService:
    """AI workflow for generating project, API, and engineering documentation."""

    def __init__(self, gemini_service: GeminiService | None = None) -> None:
        self._gemini_service = gemini_service

    def generate(self, request: DocumentationRequest) -> GeminiResponse:
        self._validate(request)
        source_context = self._build_source_context(request)
        return self._gemini().generate_documentation(
            title=request.title.strip(),
            source_context=source_context,
            audience=request.audience.strip(),
            doc_type=request.doc_type.strip(),
        )

    def _build_source_context(self, request: DocumentationRequest) -> str:
        return "\n".join(
            [
                "Primary source context:",
                request.source_context.strip(),
                "",
                "Existing documentation to preserve or improve:",
                request.existing_docs.strip() if request.existing_docs else "None",
                "",
                "Style guidelines:",
                self._format_list(request.style_guidelines),
                "",
                "Required sections:",
                self._format_list(request.include_sections),
                "",
                "Output rules:",
                "Use Markdown headings, keep claims grounded in the provided source context, and call out assumptions.",
                "Prefer concrete examples, operational caveats, and configuration notes when useful.",
            ]
        )

    def _validate(self, request: DocumentationRequest) -> None:
        if not request.title.strip():
            raise DocumentationInputError("Documentation title is required")
        if not request.source_context.strip():
            raise DocumentationInputError("Documentation source_context is required")
        if not request.audience.strip():
            raise DocumentationInputError("Documentation audience is required")
        if not request.doc_type.strip():
            raise DocumentationInputError("Documentation doc_type is required")

    def _gemini(self) -> GeminiService:
        if self._gemini_service is None:
            self._gemini_service = get_gemini_service()
        return self._gemini_service

    def _format_list(self, values: list[str]) -> str:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            return "None"
        return "\n".join(f"- {value}" for value in cleaned)


def get_documentation_service() -> DocumentationService:
    return DocumentationService()
