from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SummaryStatus(str, Enum):
    COMPLETED = "completed"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    FAILED = "failed"


class AgentRelevanceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class AgentRelevanceHint(BaseModel):
    level: AgentRelevanceLevel = AgentRelevanceLevel.UNKNOWN
    reason: str = ""


class FollowupHints(BaseModel):
    files: list[str] = Field(default_factory=list)
    directories: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class RepositorySummaryInput(BaseModel):
    repository_id: str
    full_name: str
    github_url: str
    description: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    primary_language: Optional[str] = None
    readme: Optional[str] = None
    file_tree: list[str] = Field(default_factory=list)


class SummaryLimitations(BaseModel):
    missing_inputs: list[str] = Field(default_factory=list)
    truncated_inputs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RepositoryMetadata(BaseModel):
    repository_id: Optional[str] = None
    full_name: str
    github_url: str
    description: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    primary_language: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    pushed_at: Optional[str] = None
    github_updated_at: Optional[str] = None


class SummaryGenerationOptions(BaseModel):
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None


class RepositorySummaryRequest(BaseModel):
    repository: RepositoryMetadata
    snapshot_id: Optional[str] = None
    readme_text: Optional[str] = None
    shallow_file_tree: list[str] = Field(default_factory=list)
    options: SummaryGenerationOptions = Field(default_factory=SummaryGenerationOptions)


class RepositorySummary(BaseModel):
    repository_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    full_name: str
    github_url: str
    summary_status: SummaryStatus
    one_line_summary: Optional[str] = None
    readme_summary: Optional[str] = None
    project_purpose: Optional[str] = None
    target_users: list[str] = Field(default_factory=list)
    possible_agent_relevance: AgentRelevanceHint = Field(
        default_factory=lambda: AgentRelevanceHint(
            level=AgentRelevanceLevel.UNKNOWN,
            reason="AgentHub relevance was not assessed.",
        )
    )
    followup_hints: FollowupHints = Field(default_factory=FollowupHints)
    summary_limitations: SummaryLimitations = Field(default_factory=SummaryLimitations)
    generated_at: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    error_message: Optional[str] = None
