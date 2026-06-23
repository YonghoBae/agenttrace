from __future__ import annotations

from typing import Protocol

from agenttrace.agents.analysis.state import AnalysisState


class ContentIndexStore(Protocol):
    def request_index(self, **kwargs) -> dict | None:
        ...


def content_indexer(state: AnalysisState, *, store: ContentIndexStore | None = None) -> AnalysisState:
    request = state.get("content_index_request")
    if not request:
        return {"content_index_result": {"status": "SKIPPED", "reason": "missing content_index_request"}}

    if store is None:
        return {
            "content_index_result": {
                "status": "PENDING",
                "reason": "content index store not configured",
                "request": request,
            }
        }

    result = store.request_index(**request)
    return {"content_index_result": result or {"status": "UNKNOWN"}}
