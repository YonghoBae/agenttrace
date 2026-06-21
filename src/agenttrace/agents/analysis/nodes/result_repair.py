from __future__ import annotations

from agenttrace.agents.analysis.nodes.finalize_analysis import finalize_analysis
from agenttrace.agents.analysis.state import AnalysisState


def result_repair(state: AnalysisState) -> AnalysisState:
    return finalize_analysis(state)
