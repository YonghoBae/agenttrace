"""Lightweight repository summary component."""

from agenttrace.agents.summary.schemas import (
    AgentRelevanceHint,
    AgentRelevanceLevel,
    FollowupHints,
    RepositoryMetadata,
    RepositorySummary,
    RepositorySummaryInput,
    RepositorySummaryRequest,
    SummaryGenerationOptions,
    SummaryLimitations,
    SummaryStatus,
)
from agenttrace.shared.errors import (
    MissingSummaryModelError,
    SummaryGenerationError,
    SummaryServiceError,
)
from agenttrace.models import build_openai_summary_model


def summarize_repository(*args, **kwargs):
    from agenttrace.agents.summary.service import summarize_repository as _summarize

    return _summarize(*args, **kwargs)

__all__ = [
    "AgentRelevanceHint",
    "AgentRelevanceLevel",
    "FollowupHints",
    "MissingSummaryModelError",
    "RepositoryMetadata",
    "RepositorySummary",
    "RepositorySummaryInput",
    "RepositorySummaryRequest",
    "SummaryGenerationOptions",
    "SummaryLimitations",
    "SummaryGenerationError",
    "SummaryServiceError",
    "SummaryStatus",
    "build_openai_summary_model",
    "summarize_repository",
]
