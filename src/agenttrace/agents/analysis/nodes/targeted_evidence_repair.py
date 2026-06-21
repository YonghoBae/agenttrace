from __future__ import annotations

from agenttrace.agents.analysis.state import AnalysisState


def targeted_evidence_repair(state: AnalysisState) -> AnalysisState:
    limitations = dict(state.get("analysis_limitations", {}))
    notes = list(limitations.get("notes", []))
    notes.append("targeted evidence repair skipped after deterministic pass")
    limitations["notes"] = notes
    return {"analysis_limitations": limitations}
