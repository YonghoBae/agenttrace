from __future__ import annotations

from agenttrace.agents.analysis.input_providers import AnalysisInputAssembler
from agenttrace.agents.analysis.schemas.input import AnalysisInputRequest
from agenttrace.agents.analysis.state import AnalysisState


def collect_inputs(state: AnalysisState) -> AnalysisState:
    request = AnalysisInputRequest.model_validate(state["analysis_request"])
    assembled = AnalysisInputAssembler().assemble(request)

    return {
        "run_id": str(request.analysis_id),
        "full_name": request.repository.full_name,
        "github_url": request.repository.github_url or "",
        "metadata": request.repository.model_dump(),
        "repository_snapshot": request.snapshot.model_dump() if request.snapshot else {},
        "readme": request.readme_text or "",
        "file_tree": [{"path": path} for path in request.file_tree],
        "source_files": [source.model_dump() for source in assembled.source_files],
        "missing_inputs": assembled.missing_inputs,
        "input_manifest": assembled.input_manifest,
        "analysis_mode": assembled.analysis_mode,
    }
