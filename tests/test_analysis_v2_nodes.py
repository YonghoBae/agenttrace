from agenttrace.agents.analysis.nodes.analysis_precheck import analysis_precheck
from agenttrace.agents.analysis.nodes.content_preprocessor import content_preprocessor


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
