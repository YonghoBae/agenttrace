# Summary Contract Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the AgentTrace Summary agent with the approved AgentHub artifact contract while keeping DB persistence and stored-summary APIs outside this repository.

**Architecture:** AgentTrace remains an internal Summary generation service. The caller supplies collected repository metadata, README text, shallow file tree, snapshot identity, and optional execution options; AgentTrace returns an artifact-aligned structured summary plus execution metadata. Pydantic structured output handles shape validation, while deterministic service guards enforce domain policy such as no invented follow-up paths and empty text fields for `insufficient_context`.

**Tech Stack:** Python, FastAPI, Pydantic, LangChain structured output, pytest.

---

## File Structure

- Modify: `src/agenttrace/agents/summary/schemas.py`
  - Owns Summary request/response Pydantic models and enums.
  - Replace legacy fields with artifact-aligned fields.
- Modify: `src/agenttrace/agents/summary/prompt.md`
  - Owns the repository summary prompt text.
  - Add YAML-style metadata and Korean-only output policy.
- Modify: `src/agenttrace/agents/summary/service.py`
  - Owns prompt loading, model invocation, context sufficiency checks, deterministic guards, execution metadata, and failed-summary helper.
- Modify: `src/agenttrace/agents/summary/__init__.py`
  - Re-export the new models/constants used by tests and routers.
- Modify: `src/agenttrace/app/routers/summaries.py`
  - Keep `POST /v1/repository-summaries`.
  - Update canonical endpoint to accept the new request body.
  - Keep `/from-github-url` as dev-only/deprecated and convert ingest output into the canonical request shape.
- Modify: `src/agenttrace/services/repo_ingest.py`
  - Update conversion helper to build the new Summary request shape.
- Modify: `tests/test_summary_service.py`
  - Primary service/unit coverage for schema, prompt metadata, insufficient context, guards, options, and failed helper.
- Modify: `tests/test_summary_api.py`
  - API coverage for canonical request shape and dev-only GitHub URL route compatibility.
- Modify: `tests/test_repo_ingest.py`
  - Conversion helper coverage for `readme_text` and `shallow_file_tree`.

---

## Task 1: Schema Contract

**Files:**
- Modify: `tests/test_summary_service.py`
- Modify: `src/agenttrace/agents/summary/schemas.py`
- Modify: `src/agenttrace/agents/summary/__init__.py`

- [ ] **Step 1: Write failing schema tests**

Add or update tests in `tests/test_summary_service.py` that expect the new artifact-aligned request and response models:

```python
def test_repository_summary_request_uses_artifact_aligned_shape():
    request = RepositorySummaryRequest(
        repository={
            "repository_id": "repo-1",
            "full_name": "acme/weather-agent",
            "github_url": "https://github.com/acme/weather-agent",
            "description": "Weather automation tools for agents.",
            "topics": ["mcp", "weather"],
            "primary_language": "Python",
            "stars": 120,
            "forks": 12,
            "pushed_at": "2026-06-10T12:30:00Z",
            "github_updated_at": "2026-06-10T12:30:00Z",
        },
        snapshot_id="snapshot-1",
        readme_text="# Weather Agent\nMCP weather tools.",
        shallow_file_tree=["README.md", "src/weather_agent/"],
        options={
            "model_name": "gpt-4o-mini",
            "prompt_version": "repository-summary@1.0.0",
        },
    )

    assert request.repository.full_name == "acme/weather-agent"
    assert request.readme_text.startswith("# Weather Agent")
    assert request.shallow_file_tree == ["README.md", "src/weather_agent/"]
    assert request.options.model_name == "gpt-4o-mini"
    assert request.options.prompt_version == "repository-summary@1.0.0"
```

Add a response-shape test:

```python
def test_repository_summary_response_uses_artifact_fields_only():
    summary = RepositorySummary(
        repository_id="repo-1",
        snapshot_id="snapshot-1",
        full_name="acme/weather-agent",
        github_url="https://github.com/acme/weather-agent",
        summary_status="completed",
        one_line_summary="에이전트가 날씨 정보를 조회하도록 돕는 MCP 기반 도구입니다.",
        readme_summary="README는 날씨 조회 도구와 사용 예시를 설명합니다.",
        project_purpose="에이전트 워크플로우에서 날씨 정보를 쉽게 조회하도록 돕습니다.",
        target_users=["AI agent developers", "MCP users"],
        possible_agent_relevance={
            "level": "medium",
            "reason": "README에 MCP 도구 제공이 언급됩니다.",
        },
        followup_hints={
            "files": ["README.md"],
            "directories": ["src/weather_agent"],
            "questions": ["도구 호출 구조는 어디에서 정의되는가?"],
        },
        summary_limitations={
            "missing_inputs": [],
            "truncated_inputs": [],
            "notes": ["README와 metadata 기준 요약입니다."],
        },
        generated_at="2026-06-17T00:00:00Z",
        model_name="gpt-4o-mini",
        prompt_version="repository-summary@1.0.0",
        error_message=None,
    )

    dumped = summary.model_dump()
    assert "apparent_target_users" not in dumped
    assert "readme_claims" not in dumped
    assert "summary_basis" not in dumped
    assert "confidence" not in dumped
    assert dumped["target_users"] == ["AI agent developers", "MCP users"]
    assert dumped["summary_limitations"]["missing_inputs"] == []
```

- [ ] **Step 2: Run schema tests to verify failure**

Run:

```bash
pytest tests/test_summary_service.py::test_repository_summary_request_uses_artifact_aligned_shape tests/test_summary_service.py::test_repository_summary_response_uses_artifact_fields_only -v
```

Expected: FAIL because `RepositorySummaryRequest`, nested repository/options models, and structured `summary_limitations` do not exist yet.

- [ ] **Step 3: Implement schema models**

In `src/agenttrace/agents/summary/schemas.py`:

- Keep `SummaryStatus` with only `completed`, `insufficient_context`, `failed`.
- Keep `AgentRelevanceLevel` with `high`, `medium`, `low`, `unknown`.
- Add `RepositoryMetadata`.
- Add `SummaryGenerationOptions`.
- Add `RepositorySummaryRequest`.
- Replace list `summary_limitations` with `SummaryLimitations`.
- Replace `apparent_target_users` with `target_users`.
- Remove legacy response fields: `readme_claims`, `readme_described_features`, `summary_basis`, `input_gaps`, `missing_details`, `confidence`, `possible_harness_relevance`.

Use this shape:

```python
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
    possible_agent_relevance: AgentRelevanceHint = Field(default_factory=AgentRelevanceHint)
    followup_hints: FollowupHints = Field(default_factory=FollowupHints)
    summary_limitations: SummaryLimitations = Field(default_factory=SummaryLimitations)
    generated_at: str
    model_name: Optional[str] = None
    prompt_version: str
    error_message: Optional[str] = None
```

Update `src/agenttrace/agents/summary/__init__.py` to export the new models.

- [ ] **Step 4: Run schema tests to verify pass**

Run:

```bash
pytest tests/test_summary_service.py::test_repository_summary_request_uses_artifact_aligned_shape tests/test_summary_service.py::test_repository_summary_response_uses_artifact_fields_only -v
```

Expected: PASS.

---

## Task 2: Prompt Metadata And Korean Contract

**Files:**
- Modify: `tests/test_summary_service.py`
- Modify: `src/agenttrace/agents/summary/prompt.md`
- Modify: `src/agenttrace/agents/summary/service.py`

- [ ] **Step 1: Write failing prompt tests**

Add tests:

```python
def test_summary_prompt_has_versioned_frontmatter():
    prompt = load_summary_prompt()

    assert "prompt_id: repository-summary" in prompt
    assert "prompt_version: repository-summary@1.0.0" in prompt
    assert "artifacts/current/AI_ANALYSIS_SPEC.md" in prompt


def test_summary_prompt_enforces_korean_artifact_contract():
    prompt = load_summary_prompt()

    assert "한국어 단일 문자열" in prompt
    assert "LocalizedText" in prompt
    assert "completed, insufficient_context, failed" in prompt
    assert "summary_limitations" in prompt
    assert "missing_inputs" in prompt
    assert "truncated_inputs" in prompt
    assert "notes" in prompt
```

- [ ] **Step 2: Run prompt tests to verify failure**

Run:

```bash
pytest tests/test_summary_service.py::test_summary_prompt_has_versioned_frontmatter tests/test_summary_service.py::test_summary_prompt_enforces_korean_artifact_contract -v
```

Expected: FAIL because current prompt is English and has no metadata frontmatter.

- [ ] **Step 3: Update prompt file**

Replace `src/agenttrace/agents/summary/prompt.md` with a prompt that starts with:

```markdown
---
prompt_id: repository-summary
prompt_version: repository-summary@1.0.0
contract: artifacts/current/AI_ANALYSIS_SPEC.md
purpose: Generate first-pass repository summaries from collected repository metadata, README text, and shallow file tree.
breaking_change_policy: Major version changes when output schema or required summary behavior changes; minor for meaningful behavior improvements; patch for non-behavioral wording clarifications.
---

# Repository Summary Prompt
```

The body must instruct:

- Use only repository metadata, README, topics, primary language, shallow file tree, and activity metadata.
- Return `one_line_summary`, `readme_summary`, `project_purpose` as Korean single strings, not `LocalizedText`.
- Use only `completed`, `insufficient_context`, `failed`.
- Do not use `limited`.
- Do not infer target users without README/metadata support.
- Do not invent files/directories/questions.
- `possible_agent_relevance` is a temporary hint, not score or final classification.
- `summary_limitations` is an object with `missing_inputs`, `truncated_inputs`, `notes`.
- Do not claim code execution, benchmark, security, performance, or implementation validation.

- [ ] **Step 4: Run prompt tests to verify pass**

Run:

```bash
pytest tests/test_summary_service.py::test_summary_prompt_has_versioned_frontmatter tests/test_summary_service.py::test_summary_prompt_enforces_korean_artifact_contract -v
```

Expected: PASS.

---

## Task 3: Service Contract And Guards

**Files:**
- Modify: `tests/test_summary_service.py`
- Modify: `src/agenttrace/agents/summary/service.py`

- [ ] **Step 1: Write failing service tests**

Update `FakeStructuredSummaryModel` in `tests/test_summary_service.py` to return the new `RepositorySummary` shape.

Add tests for:

```python
def test_summarize_repository_uses_options_and_returns_execution_metadata():
    request = RepositorySummaryRequest(
        repository={
            "repository_id": "repo-1",
            "full_name": "acme/weather-agent",
            "github_url": "https://github.com/acme/weather-agent",
            "description": "Weather automation tools.",
            "topics": ["mcp", "weather"],
            "primary_language": "Python",
        },
        snapshot_id="snapshot-1",
        readme_text="# Weather Agent\nMCP weather tools.",
        shallow_file_tree=["README.md", "src/weather_agent/"],
        options={
            "model_name": "gpt-test-model",
            "prompt_version": "repository-summary@1.0.0",
        },
    )

    result = summarize_repository(request, model=FakeStructuredSummaryModel())

    assert result.repository_id == "repo-1"
    assert result.snapshot_id == "snapshot-1"
    assert result.full_name == "acme/weather-agent"
    assert result.model_name == "gpt-test-model"
    assert result.prompt_version == "repository-summary@1.0.0"
    assert result.generated_at.endswith("Z")
```

Add insufficient context guard test:

```python
def test_summarize_repository_reports_insufficient_context_with_empty_text_fields():
    request = RepositorySummaryRequest(
        repository={
            "repository_id": "repo-1",
            "full_name": "acme/empty",
            "github_url": "https://github.com/acme/empty",
            "description": None,
        },
        readme_text=None,
        shallow_file_tree=[],
    )

    result = summarize_repository(request, model=None)

    assert result.summary_status == SummaryStatus.INSUFFICIENT_CONTEXT
    assert result.one_line_summary is None
    assert result.readme_summary is None
    assert result.project_purpose is None
    assert "README content" in result.summary_limitations.missing_inputs
    assert result.error_message is None
```

Add guard test:

```python
def test_summarize_repository_removes_followup_paths_outside_shallow_file_tree():
    class FakeModelWithInvalidHints(FakeStructuredSummaryModel):
        def invoke(self, payload):
            result = super().invoke(payload)
            result.followup_hints.files = ["README.md", "invented.py"]
            result.followup_hints.directories = ["src/weather_agent", "missing_dir"]
            return result

    request = RepositorySummaryRequest(
        repository={
            "repository_id": "repo-1",
            "full_name": "acme/weather-agent",
            "github_url": "https://github.com/acme/weather-agent",
            "description": "Weather automation tools.",
        },
        readme_text="# Weather Agent\nMCP weather tools.",
        shallow_file_tree=["README.md", "src/weather_agent/"],
    )

    result = summarize_repository(request, model=FakeModelWithInvalidHints())

    assert result.followup_hints.files == ["README.md"]
    assert result.followup_hints.directories == ["src/weather_agent"]
    assert any("Removed follow-up files" in note for note in result.summary_limitations.notes)
    assert any("Removed follow-up directories" in note for note in result.summary_limitations.notes)
```

Add failed helper test:

```python
def test_build_failed_summary_creates_persistable_failed_result():
    request = RepositorySummaryRequest(
        repository={
            "repository_id": "repo-1",
            "full_name": "acme/weather-agent",
            "github_url": "https://github.com/acme/weather-agent",
        }
    )

    result = build_failed_summary(
        request,
        error_message="LLM API failed.",
        model_name="gpt-test-model",
        prompt_version="repository-summary@1.0.0",
    )

    assert result.summary_status == SummaryStatus.FAILED
    assert result.error_message == "LLM API failed."
    assert result.one_line_summary is None
    assert result.summary_limitations.notes
```

- [ ] **Step 2: Run service tests to verify failure**

Run:

```bash
pytest tests/test_summary_service.py -v
```

Expected: FAIL because service still accepts `RepositorySummaryInput`, legacy fields, and list limitations.

- [ ] **Step 3: Implement service contract**

In `src/agenttrace/agents/summary/service.py`:

- Add constants:

```python
SUMMARY_PROMPT_ID = "repository-summary"
SUMMARY_PROMPT_VERSION = "repository-summary@1.0.0"
```

- Change `summarize_repository` signature to accept `RepositorySummaryRequest`.
- Resolve execution metadata:

```python
model_name = summary_request.options.model_name or settings.summary_model
prompt_version = summary_request.options.prompt_version or SUMMARY_PROMPT_VERSION
```

- Use `_has_insufficient_context(summary_request)` to return a structured `insufficient_context` result when README and description are missing or README is too short.
- Invoke `model.with_structured_output(RepositorySummary)`.
- Validate non-model dict responses through `RepositorySummary.model_validate`.
- Apply guards:
  - Preserve `repository_id`, `snapshot_id`, `full_name`, `github_url`.
  - Preserve `generated_at`, `model_name`, `prompt_version`.
  - Clear text fields when status is `insufficient_context`.
  - Merge baseline limitation notes.
  - Remove follow-up files/directories not present in `shallow_file_tree`.
- Add `build_failed_summary`.

Use `datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")` for `generated_at`.

- [ ] **Step 4: Run service tests to verify pass**

Run:

```bash
pytest tests/test_summary_service.py -v
```

Expected: PASS for summary service tests.

---

## Task 4: API And Ingest Conversion

**Files:**
- Modify: `tests/test_summary_api.py`
- Modify: `tests/test_repo_ingest.py`
- Modify: `src/agenttrace/app/routers/summaries.py`
- Modify: `src/agenttrace/services/repo_ingest.py`

- [ ] **Step 1: Write failing API tests**

Update canonical API test to post the new request shape:

```python
def test_repository_summary_endpoint_returns_summary(monkeypatch):
    monkeypatch.setattr(
        "agenttrace.app.dependencies.build_openai_summary_model",
        lambda: FakeStructuredSummaryModel(),
    )

    response = client.post(
        "/v1/repository-summaries",
        json={
            "repository": {
                "repository_id": "repo-1",
                "full_name": "acme/weather-agent",
                "github_url": "https://github.com/acme/weather-agent",
                "description": "Weather automation tools.",
                "topics": ["mcp", "weather"],
                "primary_language": "Python",
            },
            "snapshot_id": "snapshot-1",
            "readme_text": "# Weather Agent\nMCP weather tools.",
            "shallow_file_tree": ["README.md", "src/weather_agent/"],
            "options": {"model_name": "gpt-test-model"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary_status"] == "completed"
    assert body["target_users"] == ["AI agent developers", "MCP users"]
    assert body["model_name"] == "gpt-test-model"
    assert body["prompt_version"] == "repository-summary@1.0.0"
    assert "apparent_target_users" not in body
```

Update GitHub URL route test to assert it still works but emits the new request object into `summarize_repository`.

Update `tests/test_repo_ingest.py`:

```python
def test_repo_digest_to_summary_request_truncates_large_content_payload():
    digest = RepoDigest(...)
    request = repo_digest_to_summary_request(digest, fallback_full_name="obra/superpowers")

    assert request.repository.full_name == "obra/superpowers"
    assert request.readme_text is not None
    assert "Truncated by AgentTrace" in request.readme_text
    assert request.shallow_file_tree == ["README.md"]
```

- [ ] **Step 2: Run API/ingest tests to verify failure**

Run:

```bash
pytest tests/test_summary_api.py tests/test_repo_ingest.py -v
```

Expected: FAIL because router and ingest helper still use legacy input names.

- [ ] **Step 3: Implement API and ingest conversion**

In `src/agenttrace/app/routers/summaries.py`:

- Change canonical endpoint parameter to `RepositorySummaryRequest`.
- Keep route path `@router.post("/repository-summaries", response_model=RepositorySummary)`.
- Build model using resolved request options where needed.
- Keep `/repository-summaries/from-github-url`.
- Mark the GitHub URL route with a docstring or `deprecated=True` in router decorator if FastAPI supports it in this codebase:

```python
@router.post(
    "/repository-summaries/from-github-url",
    response_model=RepositorySummary,
    deprecated=True,
)
```

In `src/agenttrace/services/repo_ingest.py`:

- Rename or add `repo_digest_to_summary_request`.
- Return `RepositorySummaryRequest`.
- Map `digest.readme` to `readme_text`.
- Map `digest.file_tree` to `shallow_file_tree`.
- Build `repository={...}`.

- [ ] **Step 4: Run API/ingest tests to verify pass**

Run:

```bash
pytest tests/test_summary_api.py tests/test_repo_ingest.py -v
```

Expected: PASS for API and ingest tests.

---

## Task 5: Focused And Full Verification

**Files:**
- No source edits unless verification reveals a defect.

- [ ] **Step 1: Run focused Summary verification**

Run:

```bash
pytest tests/test_summary_service.py tests/test_summary_api.py tests/test_repo_ingest.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
pytest
```

Expected: PASS. If failures are unrelated to Summary contract changes, record exact failing tests and inspect before deciding whether to fix.

- [ ] **Step 3: Review diff for scope**

Run:

```bash
git diff -- src/agenttrace/agents/summary src/agenttrace/app/routers/summaries.py src/agenttrace/services/repo_ingest.py tests/test_summary_service.py tests/test_summary_api.py tests/test_repo_ingest.py docs/superpowers/plans/2026-06-17-summary-contract-alignment.md
```

Expected: Diff only contains Summary contract alignment and the plan artifact.

---

## Self-Review

- Spec coverage: The plan covers agent-only boundary, artifact-aligned schema, request shape, options-based model/prompt override, semantic prompt version metadata, Korean text policy, insufficient-context empty text fields, deterministic guards, HTTP failure behavior, failed-summary helper, current route preservation, and dev-only GitHub URL route.
- Placeholder scan: No implementation step leaves unspecified work. Each code-related step names concrete files, models, fields, and expected commands.
- Type consistency: The request model is consistently named `RepositorySummaryRequest`; response model remains `RepositorySummary`; `readme_text` and `shallow_file_tree` are used instead of legacy `readme` and `file_tree`; `SummaryLimitations` is consistently structured as `missing_inputs`, `truncated_inputs`, and `notes`.
