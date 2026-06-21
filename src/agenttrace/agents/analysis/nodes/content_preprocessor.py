from __future__ import annotations

from agenttrace.agents.analysis.chunking import build_chunk_index, chunk_source_files
from agenttrace.agents.analysis.schemas.input import SourceFile
from agenttrace.agents.analysis.state import AnalysisState


def content_preprocessor(state: AnalysisState) -> AnalysisState:
    source_files = [
        SourceFile.model_validate(item)
        for item in state.get("source_files", [])
    ]
    chunks = chunk_source_files(source_files)
    index = build_chunk_index(chunks)

    return {
        "content_chunks": [chunk.model_dump() for chunk in chunks],
        "chunk_index": index.model_dump(),
    }
