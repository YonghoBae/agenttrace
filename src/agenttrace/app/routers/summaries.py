from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from agenttrace.agents.summary import RepositorySummary, RepositorySummaryInput
from agenttrace.agents.summary.service import requires_llm_summary, summarize_repository
from agenttrace.app.dependencies import get_summary_model_factory
from agenttrace.app.errors import summary_service_exception_to_http

router = APIRouter(tags=["summaries"])


@router.post("/repository-summaries", response_model=RepositorySummary)
def create_repository_summary(
    summary_input: RepositorySummaryInput,
    summary_model_factory: Annotated[Callable[[], Any], Depends(get_summary_model_factory)],
) -> RepositorySummary:
    try:
        model = summary_model_factory() if requires_llm_summary(summary_input) else None
        return summarize_repository(summary_input, model=model)
    except Exception as exc:
        raise summary_service_exception_to_http(exc) from exc
