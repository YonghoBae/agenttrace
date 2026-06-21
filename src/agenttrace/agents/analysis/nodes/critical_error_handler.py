from __future__ import annotations

from agenttrace.agents.analysis.state import AnalysisState


def critical_error_handler(state: AnalysisState) -> AnalysisState:
    errors = state.get("quality_gate_result", {}).get("critical_errors") or []
    if not errors and state.get("error_message"):
        errors = [state["error_message"]]
    message = "; ".join(errors) if errors else "Analysis failed."
    return {
        "status": "FAILED",
        "error_message": message,
        "callback_payload": {
            "analysis_id": state.get("run_id"),
            "status": "FAILED",
            "analysis_result": None,
            "error_message": message,
        },
    }
