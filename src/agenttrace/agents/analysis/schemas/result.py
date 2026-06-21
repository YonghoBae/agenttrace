from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LocalizedText(BaseModel):
    ko: str
    en: str


class AnalysisLimitations(BaseModel):
    missing_inputs: list[str] = Field(default_factory=list)
    truncated_inputs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AnalysisClaim(BaseModel):
    claim_id: str
    claim_text: str
    source_path: str = "README.md"
    source_section: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_signal_ids: list[str] = Field(default_factory=list)


class EvidenceSignal(BaseModel):
    signal_id: str
    signal_type: str
    path: str
    chunk_id: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    content_excerpt: str | None = None
    content_hash: str | None = None
    summary: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ClaimVerdict(BaseModel):
    claim_id: str
    verdict: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "NOT_FOUND", "INSUFFICIENT_EVIDENCE", "DOCUMENTED"]
    reason: str
    evidence_signal_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class EvidenceTaskResult(BaseModel):
    task_id: str
    status: Literal["RESOLVED", "INSUFFICIENT_EVIDENCE"]
    claim_verdicts: list[ClaimVerdict]
    evidence_signal_ids: list[str] = Field(default_factory=list)
    search_limit_reached: bool = False
    limitations: list[str] = Field(default_factory=list)


class RiskSignal(BaseModel):
    risk_type: str
    summary: str
    severity: Literal["low", "medium", "high"] = "low"


class AnalysisResult(BaseModel):
    analysis_status: Literal["completed", "completed_with_limitations", "insufficient_evidence", "uncertain_classification"]
    agent_type: Literal["MCP", "Skill", "Eval", "ToolUse", "Framework", "Other", "Unknown"] | None = None
    tech_stack_summary: LocalizedText | None = None
    analysis_claims: list[AnalysisClaim]
    evidence_signals: list[EvidenceSignal]
    evidence_task_results: list[EvidenceTaskResult]
    risk_signals: list[RiskSignal]
    follow_up_guide: LocalizedText | None = None
    analysis_limitations: AnalysisLimitations
