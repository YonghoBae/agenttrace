from pathlib import Path

from agenttrace.agents.analysis.chunking import build_chunk_index, chunk_source_files
from agenttrace.agents.analysis.schemas.input import SourceFile
from agenttrace.agents.analysis.state import AnalysisState


def content_preprocessor(state: AnalysisState) -> AnalysisState:
    local_repo_dir_str = state.get("local_repo_dir")
    local_repo_dir = Path(local_repo_dir_str) if local_repo_dir_str else None

    source_files = []
    for item in state.get("source_files", []):
        path_str = item.get("path")
        content = item.get("content") or ""

        if local_repo_dir and path_str:
            try:
                resolved_base = local_repo_dir.resolve()
                resolved_target = (local_repo_dir / path_str).resolve()
                if not resolved_target.is_relative_to(resolved_base):
                    raise ValueError(f"Path traversal detected: {path_str}")
                file_path = local_repo_dir / path_str
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                if "Path traversal detected" in str(exc):
                    raise

        validated_item = dict(item)
        validated_item["content"] = content
        source_files.append(SourceFile.model_validate(validated_item))

    chunks = chunk_source_files(source_files)
    index = build_chunk_index(chunks)

    # Strip chunk contents to keep state light
    state_chunks = []
    for chunk in chunks:
        chunk_dict = chunk.model_dump()
        chunk_dict["content"] = ""
        state_chunks.append(chunk_dict)

    index_dict = index.model_dump()
    for chunk_id, chunk_dict in index_dict.get("chunks_by_id", {}).items():
        chunk_dict["content"] = ""

    return {
        "content_chunks": state_chunks,
        "chunk_index": index_dict,
    }
