from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchAttemptTrace(BaseModel):
    attempt: int
    queries: list[str] = Field(default_factory=list)
    candidate_chunk_ids: list[str] = Field(default_factory=list)
    selected_chunk_ids: list[str] = Field(default_factory=list)
    excluded_chunk_ids: list[str] = Field(default_factory=list)
    exclusion_reasons: dict[str, str] = Field(default_factory=dict)


class TaskTrace(BaseModel):
    task_id: str
    required: bool
    search_attempts: list[SearchAttemptTrace] = Field(default_factory=list)
    task_parts: list[dict[str, Any]] = Field(default_factory=list)
    task_result: dict[str, Any] = Field(default_factory=dict)


class AnalysisRunTrace(BaseModel):
    run_id: str
    analysis_version: str = "analysis-v2"
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_info: dict[str, Any] = Field(default_factory=dict)
    input_manifest: dict[str, Any] = Field(default_factory=dict)
    precheck_result: dict[str, Any] = Field(default_factory=dict)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    analysis_plan: dict[str, Any] = Field(default_factory=dict)
    task_traces: list[TaskTrace] = Field(default_factory=list)
    final_result: dict[str, Any] = Field(default_factory=dict)
    quality_gate_result: dict[str, Any] = Field(default_factory=dict)
    timing: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
