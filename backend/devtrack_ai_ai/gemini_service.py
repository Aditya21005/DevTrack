from __future__ import annotations

import logging
import os
import random
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _env_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return default

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'")
    return default


class GeminiServiceError(RuntimeError):
    """Base Gemini service error."""


class GeminiConfigurationError(GeminiServiceError):
    """Raised when Gemini configuration or dependencies are missing."""


class GeminiRateLimitError(GeminiServiceError):
    """Raised when the local rate limiter rejects a request."""


class GeminiProviderError(GeminiServiceError):
    """Raised when Gemini returns an error after retries are exhausted."""


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str = field(repr=False)
    model: str
    timeout_seconds: float
    max_retries: int
    retry_base_delay_seconds: float
    retry_max_delay_seconds: float
    rate_limit_per_minute: int
    temperature: float
    max_output_tokens: int

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        api_key = _env_value("GEMINI_API_KEY").strip()
        if not api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY environment variable is required")
        return cls(
            api_key=api_key,
            model=_env_value("GEMINI_MODEL", "gemini-3.5-flash").strip(),
            timeout_seconds=float(_env_value("GEMINI_TIMEOUT_SECONDS", "30")),
            max_retries=int(_env_value("GEMINI_MAX_RETRIES", "3")),
            retry_base_delay_seconds=float(_env_value("GEMINI_RETRY_BASE_DELAY_SECONDS", "0.5")),
            retry_max_delay_seconds=float(_env_value("GEMINI_RETRY_MAX_DELAY_SECONDS", "8")),
            rate_limit_per_minute=int(_env_value("GEMINI_RATE_LIMIT_PER_MINUTE", "60")),
            temperature=float(_env_value("GEMINI_TEMPERATURE", "0.2")),
            max_output_tokens=int(_env_value("GEMINI_MAX_OUTPUT_TOKENS", "2048")),
        )


@dataclass(frozen=True)
class GeminiResponse:
    text: str
    model: str
    usage: dict[str, Any]
    raw: Any | None = None


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            raise GeminiConfigurationError("Gemini rate limit must be greater than zero")
        self.limit = limit
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        now = time.monotonic()
        with self._lock:
            while self._timestamps and now - self._timestamps[0] >= self.window_seconds:
                self._timestamps.popleft()
            if len(self._timestamps) >= self.limit:
                raise GeminiRateLimitError("Gemini local rate limit exceeded")
            self._timestamps.append(now)


class GeminiService:
    """Singleton Gemini integration service.

    The client is loaded lazily so application startup does not fail during unit
    tests that do not exercise Gemini. Runtime calls require the `google-genai`
    package and GEMINI_API_KEY.
    """

    _instance: "GeminiService | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "GeminiService":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, config: GeminiConfig | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self.config = config or GeminiConfig.from_env()
        self._client: Any | None = None
        self._client_lock = threading.Lock()
        self._rate_limiter = SlidingWindowRateLimiter(self.config.rate_limit_per_minute)
        self._initialized = True

    def breakdown_task(self, *, title: str, description: str | None = None, context: str | None = None) -> GeminiResponse:
        prompt = self._wrap_prompt(
            "Task Breakdown",
            f"""
Break this engineering task into clear implementation steps.

Task title: {title}
Description: {description or "No description provided"}
Context: {context or "No additional context provided"}

Return:
- concise subtasks
- acceptance criteria
- risks or blockers
- suggested implementation order
""",
        )
        return self._generate(prompt)

    def generate_documentation(
        self,
        *,
        title: str,
        source_context: str,
        audience: str = "developers",
        doc_type: str = "technical documentation",
    ) -> GeminiResponse:
        prompt = self._wrap_prompt(
            "Documentation Generation",
            f"""
Generate {doc_type} for {audience}.

Title: {title}
Source context:
{source_context}

Return production-ready documentation with headings, examples where useful, and clear operational notes.
""",
        )
        return self._generate(prompt)

    def plan_sprint(
        self,
        *,
        sprint_name: str,
        goals: list[str],
        candidate_tasks: list[dict[str, Any]],
        capacity_notes: str | None = None,
    ) -> GeminiResponse:
        prompt = self._wrap_prompt(
            "Sprint Planning",
            f"""
Create a practical sprint plan.

Sprint: {sprint_name}
Goals: {self._format_list(goals)}
Capacity notes: {capacity_notes or "No capacity notes provided"}
Candidate tasks: {candidate_tasks}

Return:
- recommended sprint scope
- task sequencing
- risks
- tradeoffs
- tasks to defer
""",
        )
        return self._generate(prompt)

    def daily_summary(
        self,
        *,
        summary_date: date | str,
        completed: list[str],
        in_progress: list[str],
        blockers: list[str] | None = None,
    ) -> GeminiResponse:
        prompt = self._wrap_prompt(
            "Daily Summary",
            f"""
Prepare a concise developer daily summary for {summary_date}.

Completed: {self._format_list(completed)}
In progress: {self._format_list(in_progress)}
Blockers: {self._format_list(blockers or [])}

Return:
- summary paragraph
- accomplishments
- current focus
- blockers and asks
- next steps
""",
        )
        return self._generate(prompt)

    def _generate(self, prompt: str) -> GeminiResponse:
        self._rate_limiter.acquire()
        return self._with_retries(lambda: self._with_timeout(lambda: self._call_gemini(prompt)))

    def _call_gemini(self, prompt: str) -> GeminiResponse:
        client = self._get_client()
        try:
            if hasattr(client, "interactions"):
                response = client.interactions.create(model=self.config.model, input=prompt)
            elif hasattr(client, "models"):
                response = client.models.generate_content(model=self.config.model, contents=prompt)
            else:
                raise GeminiConfigurationError("Unsupported google-genai client: missing interactions/models API")
        except Exception as exc:
            raise GeminiProviderError("Gemini provider request failed") from exc

        text = self._extract_text(response)
        usage = self._extract_usage(response)
        return GeminiResponse(text=text, model=self.config.model, usage=usage, raw=response)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        with self._client_lock:
            if self._client is not None:
                return self._client
            try:
                from google import genai  # type: ignore import-not-found
            except Exception as exc:
                raise GeminiConfigurationError("Install google-genai to use GeminiService") from exc
            try:
                self._client = genai.Client(api_key=self.config.api_key)
            except TypeError:
                os.environ.setdefault("GEMINI_API_KEY", self.config.api_key)
                self._client = genai.Client()
            return self._client

    def _with_timeout(self, operation: Callable[[], T]) -> T:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(operation)
            try:
                return future.result(timeout=self.config.timeout_seconds)
            except FutureTimeoutError as exc:
                raise GeminiProviderError("Gemini provider request timed out") from exc

    def _with_retries(self, operation: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                return operation()
            except GeminiConfigurationError:
                raise
            except GeminiRateLimitError:
                raise
            except GeminiProviderError as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                delay = self._retry_delay(attempt)
                logger.warning("gemini.retry", extra={"attempt": attempt + 1, "delay_seconds": delay})
                time.sleep(delay)
        raise GeminiProviderError("Gemini request failed after retries") from last_error

    def _retry_delay(self, attempt: int) -> float:
        exponential = self.config.retry_base_delay_seconds * (2**attempt)
        capped = min(exponential, self.config.retry_max_delay_seconds)
        jitter = random.uniform(0, capped * 0.25)
        return capped + jitter

    def _extract_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text).strip()
        text = getattr(response, "text", None)
        if text:
            return str(text).strip()
        raise GeminiProviderError("Gemini response did not include text output")

    def _extract_usage(self, response: Any) -> dict[str, Any]:
        usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)
        if usage is None:
            return {}
        if hasattr(usage, "model_dump"):
            return dict(usage.model_dump())
        if isinstance(usage, dict):
            return usage
        return {key: getattr(usage, key) for key in dir(usage) if key.endswith("tokens") and not key.startswith("_")}

    def _wrap_prompt(self, task_type: str, body: str) -> str:
        return f"""
You are DevTrack AI's senior engineering assistant.
Task type: {task_type}

Rules:
- Be specific and actionable.
- Do not invent unavailable project facts.
- Prefer concise structured output.
- Highlight assumptions clearly.

{body.strip()}
""".strip()

    def _format_list(self, values: list[str]) -> str:
        if not values:
            return "None"
        return "\n".join(f"- {value}" for value in values)


def get_gemini_service() -> GeminiService:
    return GeminiService()


