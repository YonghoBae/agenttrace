from agenttrace.agents.analysis.nodes.analysis_precheck import analysis_precheck
from agenttrace.agents.analysis.nodes.analysis_planner import analysis_planner
from agenttrace.agents.analysis.nodes.claim_analyzer import claim_analyzer
from agenttrace.agents.analysis.nodes.content_preprocessor import content_preprocessor
from agenttrace.agents.analysis.nodes.evidence_evaluator import evidence_evaluator
from agenttrace.agents.analysis.nodes.evidence_scout import evidence_scout
from agenttrace.agents.analysis.nodes.finalize_task import finalize_task
from agenttrace.agents.analysis.nodes.request_builder import request_builder
from agenttrace.agents.analysis.nodes.task_result_merge import task_result_merge


def test_content_preprocessor_builds_chunks_from_source_files():
    state = {
        "source_files": [{"path": "src/server.py", "content": "def register_tool(): pass"}],
        "missing_inputs": [],
    }

    result = content_preprocessor(state)

    assert result["content_chunks"]
    assert result["chunk_index"]["entries"][0]["file_path"] == "src/server.py"


def test_analysis_precheck_allows_limited_readme_file_tree_analysis():
    state = {
        "readme": "# Repo\nProvides MCP tools.",
        "file_tree": [{"path": "src/server.py"}],
        "missing_inputs": ["source_files"],
        "content_chunks": [],
    }

    result = analysis_precheck(state)

    assert result["precheck_result"]["can_analyze"] is True
    assert result["analysis_mode"] == "limited"
    assert "source_files" in result["analysis_limitations"]["missing_inputs"]


def test_claim_analyzer_extracts_readme_claims_without_summary_regeneration():
    result = claim_analyzer(
        {"readme": "# Repo\nProvides an MCP server.\nSupports tool registration."}
    )

    assert [claim["claim_id"] for claim in result["claims"]] == ["claim-1", "claim-2"]
    assert "MCP server" in result["claims"][0]["claim_text"]


def test_analysis_planner_groups_claims_into_required_tasks():
    result = analysis_planner(
        {
            "metadata": {"repository_id": "repo-1"},
            "claims": [
                {"claim_id": "claim-1", "claim_text": "Provides an MCP server.", "source_path": "README.md"},
                {"claim_id": "claim-2", "claim_text": "Supports tool registration.", "source_path": "README.md"},
            ],
            "file_tree": [{"path": "src/server.py"}, {"path": "README.md"}],
        }
    )

    task = result["analysis_plan"]["tasks"][0]
    assert task["required"] is True
    assert task["status"] == "PENDING"
    assert "claim-1" in task["claims"]


def _state_with_task_and_chunk():
    return {
        "current_task_id": "task-1",
        "analysis_plan": {
            "tasks": [
                {
                    "task_id": "task-1",
                    "claims": ["claim-1"],
                    "target_paths": ["src/server.py"],
                    "required": True,
                    "status": "PENDING",
                }
            ]
        },
        "claims": [{"claim_id": "claim-1", "claim_text": "Provides an MCP server."}],
        "chunk_index": {
            "entries": [
                {
                    "file_path": "src/server.py",
                    "chunk_ids": ["chunk-0001"],
                    "keywords": ["server", "mcp"],
                    "chunk_count": 1,
                }
            ],
            "chunks_by_id": {
                "chunk-0001": {
                    "chunk_id": "chunk-0001",
                    "file_path": "src/server.py",
                    "content": "class McpServer: pass",
                    "start_byte": 0,
                    "end_byte": 21,
                    "line_start": 1,
                    "line_end": 1,
                    "is_partial": False,
                    "content_hash": "sha256:"
                    + "0" * 64,
                }
            },
        },
        "task_traces": [],
    }


def test_evidence_task_loop_resolves_supported_claim():
    state = _state_with_task_and_chunk()
    state.update(evidence_scout(state))
    state.update(request_builder(state))
    state.update(evidence_evaluator(state))
    state.update(task_result_merge(state))
    result = finalize_task(state)

    task_result = result["task_results"][0]
    assert task_result["status"] == "RESOLVED"
    assert task_result["claim_verdicts"][0]["verdict"] in {"SUPPORTED", "PARTIALLY_SUPPORTED"}
