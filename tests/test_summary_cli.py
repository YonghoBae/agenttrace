from __future__ import annotations

import json

import pytest

from agenttrace.agents.summary.cli import main
from agenttrace.shared.errors import MissingSummaryModelError, SummaryGenerationError


class FakeStructuredSummaryModel:
    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, _payload):
        return self.schema(
            full_name="ignored/llm-output",
            github_url="https://github.com/ignored/llm-output",
            summary_status="completed",
            one_line_summary="Weather Agent appears to provide weather automation tools.",
            readme_summary="Weather Agent is presented as an MCP-style weather automation project.",
            project_purpose="Provide weather automation helpers for agent workflows.",
            target_users=["agent developers", "MCP users"],
            possible_agent_relevance={
                "level": "medium",
                "reason": "README mentions agent workflows.",
            },
        )


def _summary_request_payload() -> dict:
    return {
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
        "shallow_file_tree": ["README.md"],
        "options": {"model_name": "gpt-test-model"},
    }


def test_summary_cli_writes_summary_to_stdout(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "summary-request.json"
    input_path.write_text(json.dumps(_summary_request_payload()), encoding="utf-8")
    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.build_openai_summary_model",
        lambda: FakeStructuredSummaryModel(),
    )

    main([str(input_path)])

    body = json.loads(capsys.readouterr().out)
    assert body["repository_id"] == "repo-1"
    assert body["snapshot_id"] == "snapshot-1"
    assert body["full_name"] == "acme/weather-agent"
    assert body["summary_status"] == "completed"
    assert body["model_name"] == "gpt-test-model"


def test_summary_cli_writes_summary_to_output_file(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "summary-request.json"
    output_path = tmp_path / "summary-result.json"
    input_path.write_text(json.dumps(_summary_request_payload()), encoding="utf-8")
    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.build_openai_summary_model",
        lambda: FakeStructuredSummaryModel(),
    )

    main([str(input_path), "--output", str(output_path)])

    assert capsys.readouterr().out == ""
    body = json.loads(output_path.read_text(encoding="utf-8"))
    assert body["repository_id"] == "repo-1"
    assert body["summary_status"] == "completed"


def test_summary_cli_skips_model_when_context_is_insufficient(
    tmp_path,
    capsys,
    monkeypatch,
):
    input_path = tmp_path / "summary-request.json"
    input_path.write_text(
        json.dumps(
            {
                "repository": {
                    "repository_id": "repo-1",
                    "full_name": "acme/weather-agent",
                    "github_url": "https://github.com/acme/weather-agent",
                }
            }
        ),
        encoding="utf-8",
    )

    def fail_build_model():
        raise AssertionError("model should not be built")

    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.build_openai_summary_model",
        fail_build_model,
    )

    main([str(input_path)])

    body = json.loads(capsys.readouterr().out)
    assert body["summary_status"] == "insufficient_context"


def test_summary_cli_reports_invalid_request_json(tmp_path, capsys):
    input_path = tmp_path / "summary-request.json"
    input_path.write_text(json.dumps({"repository": {}}), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_path)])

    assert exc_info.value.code == 2
    assert "Invalid RepositorySummaryRequest JSON" in capsys.readouterr().err


def test_summary_cli_reports_summary_service_error(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "summary-request.json"
    input_path.write_text(json.dumps(_summary_request_payload()), encoding="utf-8")

    def fail_summarize(_request, **_kwargs):
        raise SummaryGenerationError("Repository summary generation failed.")

    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.build_openai_summary_model",
        lambda: FakeStructuredSummaryModel(),
    )
    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.summarize_repository",
        fail_summarize,
    )

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_path)])

    assert exc_info.value.code == 1
    assert "Summary generation failed:" in capsys.readouterr().err


def test_summary_cli_reports_model_builder_configuration_error(
    tmp_path,
    capsys,
    monkeypatch,
):
    input_path = tmp_path / "summary-request.json"
    input_path.write_text(json.dumps(_summary_request_payload()), encoding="utf-8")

    def fail_build_model():
        raise MissingSummaryModelError("OPENAI_API_KEY is required for summary generation.")

    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.build_openai_summary_model",
        fail_build_model,
    )

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_path)])

    assert exc_info.value.code == 1
    assert "OPENAI_API_KEY is required" in capsys.readouterr().err


def test_summary_cli_reports_output_file_write_error(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "summary-request.json"
    blocked_parent = tmp_path / "blocked"
    output_path = blocked_parent / "summary-result.json"
    input_path.write_text(json.dumps(_summary_request_payload()), encoding="utf-8")
    blocked_parent.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(
        "agenttrace.agents.summary.cli.build_openai_summary_model",
        lambda: FakeStructuredSummaryModel(),
    )

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_path), "--output", str(output_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Failed to write summary output:" in captured.err
