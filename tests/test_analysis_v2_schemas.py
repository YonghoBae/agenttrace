import pytest
from pydantic import ValidationError

from agenttrace.agents.analysis.schemas.input import AnalysisInputRequest, SourceFile
from agenttrace.agents.analysis.schemas.content import ContentChunk
from agenttrace.agents.analysis.schemas.result import AnalysisResult, ClaimVerdict


def test_analysis_input_accepts_backend_payload_without_source_files():
    req = AnalysisInputRequest.model_validate(
        {
            "analysis_id": "00000000-0000-0000-0000-000000000001",
            "repository": {
                "repository_id": "repo-1",
                "full_name": "owner/repo",
                "github_url": "https://github.com/owner/repo",
                "description": "Agent repo",
            },
            "snapshot": {"snapshot_id": "snap-1", "commit_sha": "abc", "captured_at": "2026-06-20T00:00:00Z"},
            "readme_text": "# Repo\nProvides an MCP server.",
            "file_tree": ["README.md", "src/server.py"],
            "summary_result": {"summary_status": "completed"},
            "external_ingest": {"enabled": False, "provider": "gitingest"},
        }
    )

    assert req.source_files == []
    assert req.external_ingest.enabled is False


def test_source_file_hash_is_computed_when_missing():
    src = SourceFile(path="src/server.py", content="print('hi')")
    assert src.content_hash.startswith("sha256:")


def test_source_file_rejects_invalid_supplied_hash():
    with pytest.raises(ValidationError):
        SourceFile(path="src/server.py", content="print('hi')", content_hash="sha256:bad")


def test_source_file_rejects_hash_that_does_not_match_content():
    with pytest.raises(ValidationError):
        SourceFile(
            path="src/server.py",
            content="print('hi')",
            content_hash="sha256:0000000000000000000000000000000000000000000000000000000000000000",
        )


def test_source_file_normalizes_supplied_hash_to_lowercase():
    src = SourceFile(path="src/server.py", content="print('hi')")
    supplied = "sha256:" + src.content_hash.removeprefix("sha256:").upper()

    validated = SourceFile(path="src/server.py", content="print('hi')", content_hash=supplied)

    assert validated.content_hash == src.content_hash


def test_content_chunk_rejects_invalid_offsets_and_line_ranges():
    valid_chunk = {
        "chunk_id": "chunk-1",
        "file_path": "src/server.py",
        "content": "print('hi')",
        "start_byte": 0,
        "end_byte": 11,
        "line_start": 1,
        "line_end": 1,
        "is_partial": False,
        "content_hash": "sha256:abc",
    }

    invalid_values = [
        {"start_byte": -1},
        {"end_byte": -1},
        {"line_start": 0},
        {"line_end": 0},
        {"start_byte": 12},
        {"line_start": 2},
    ]

    for invalid_value in invalid_values:
        with pytest.raises(ValidationError):
            ContentChunk.model_validate(valid_chunk | invalid_value)


def test_analysis_result_requires_evidence_task_results():
    result = AnalysisResult.model_validate(
        {
            "analysis_status": "insufficient_evidence",
            "agent_type": "MCP",
            "tech_stack_summary": {"ko": "Python 기반", "en": "Python based"},
            "analysis_claims": [],
            "evidence_signals": [],
            "evidence_task_results": [],
            "risk_signals": [],
            "follow_up_guide": {"ko": "README와 src를 확인하세요.", "en": "Check README and src."},
            "analysis_limitations": {"missing_inputs": ["source_files"], "notes": ["limited analysis"]},
        }
    )
    assert result.analysis_status == "insufficient_evidence"


def test_claim_verdict_enum_matches_contract():
    verdict = ClaimVerdict(
        claim_id="claim-1",
        verdict="INSUFFICIENT_EVIDENCE",
        reason="Source content unavailable.",
        evidence_signal_ids=[],
        limitations=["gitingest failed"],
    )
    assert verdict.verdict == "INSUFFICIENT_EVIDENCE"


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_analysis_claim_rejects_confidence_outside_unit_interval(confidence):
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            {
                "analysis_status": "completed",
                "agent_type": "MCP",
                "tech_stack_summary": {"ko": "Python 기반", "en": "Python based"},
                "analysis_claims": [
                    {
                        "claim_id": "claim-1",
                        "claim_text": "Provides an MCP server.",
                        "confidence": confidence,
                    }
                ],
                "evidence_signals": [],
                "evidence_task_results": [],
                "risk_signals": [],
                "follow_up_guide": {"ko": "README를 확인하세요.", "en": "Check README."},
                "analysis_limitations": {"missing_inputs": [], "notes": []},
            }
        )


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_evidence_signal_rejects_confidence_outside_unit_interval(confidence):
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            {
                "analysis_status": "completed",
                "agent_type": "MCP",
                "tech_stack_summary": {"ko": "Python 기반", "en": "Python based"},
                "analysis_claims": [],
                "evidence_signals": [
                    {
                        "signal_id": "signal-1",
                        "signal_type": "source",
                        "path": "src/server.py",
                        "summary": "Server entrypoint.",
                        "confidence": confidence,
                    }
                ],
                "evidence_task_results": [],
                "risk_signals": [],
                "follow_up_guide": {"ko": "README를 확인하세요.", "en": "Check README."},
                "analysis_limitations": {"missing_inputs": [], "notes": []},
            }
        )
