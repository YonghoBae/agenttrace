from __future__ import annotations

import re

from agenttrace.agents.analysis.schemas.result import ClaimVerdict, EvidenceSignal
from agenttrace.agents.analysis.state import AnalysisState


def _current_task(state: AnalysisState) -> dict | None:
    task_id = state.get("current_task_id")
    for task in state.get("analysis_plan", {}).get("tasks", []):
        if task.get("task_id") == task_id:
            return task
    return None


def _tokens(text: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return {token.lower() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", spaced)}


def evidence_evaluator(state: AnalysisState) -> AnalysisState:
    task = _current_task(state)
    if not task:
        return {"task_part_results": []}

    chunks = state.get("selected_chunks", [])
    chunk_text = "\n".join(
        f"{chunk.get('file_path', '')}\n{chunk.get('content', '')}"
        for chunk in chunks
    )
    chunk_tokens = _tokens(chunk_text)
    claims = [
        claim for claim in state.get("claims", [])
        if claim.get("claim_id") in set(task.get("claims", []))
    ]

    evidence_signals: list[dict] = []
    verdicts: list[dict] = []
    for claim in claims:
        claim_tokens = _tokens(claim.get("claim_text", ""))
        overlap = claim_tokens & chunk_tokens
        signal_ids: list[str] = []
        if chunks and overlap:
            chunk = chunks[0]
            signal = EvidenceSignal(
                signal_id=f"signal-{len(evidence_signals) + 1:04d}",
                signal_type="SOURCE_CHUNK",
                path=chunk["file_path"],
                chunk_id=chunk["chunk_id"],
                line_start=chunk["line_start"],
                line_end=chunk["line_end"],
                content_excerpt=chunk.get("content", "")[:500],
                content_hash=chunk["content_hash"],
                summary="Source chunk overlaps README claim keywords.",
                confidence=min(0.55 + (0.05 * len(overlap)), 0.9),
            )
            evidence_signals.append(signal.model_dump())
            signal_ids.append(signal.signal_id)
            verdict = "SUPPORTED" if len(overlap) >= 2 else "PARTIALLY_SUPPORTED"
            reason = "Selected source chunk contains terms related to the claim."
            limitations: list[str] = []
        else:
            verdict = "INSUFFICIENT_EVIDENCE"
            reason = "No source chunk was available for this claim."
            limitations = ["source content unavailable or no relevant chunk selected"]

        verdicts.append(ClaimVerdict(
            claim_id=claim["claim_id"],
            verdict=verdict,
            reason=reason,
            evidence_signal_ids=signal_ids,
            limitations=limitations,
        ).model_dump())

    return {
        "task_part_results": [{
            "task_id": task["task_id"],
            "evidence_signals": evidence_signals,
            "claim_verdicts": verdicts,
        }]
    }
