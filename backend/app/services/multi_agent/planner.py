"""
Planning Layer.

Generates a human-readable plan before execution so the UI can display
what steps the agent intends to run. The plan is built from:
  - which source types are present (pdf / image / audio / text)
  - the detected intent (comparison, summarize, code_explanation, etc.)

Plans are cheap to generate (no LLM call) — just deterministic logic.
"""

from __future__ import annotations

from typing import List

from app.models.schemas import ExtractedSource, PlanStep


def build_plan(sources: List[ExtractedSource], intent: str) -> List[PlanStep]:
    """
    Return an ordered list of PlanStep objects based on what inputs are present
    and what the detected intent is.
    """
    steps: list[PlanStep] = []
    step_num = 0

    types_present = {s.source_type for s in sources if s.status != "failed"}

    def add(tool: str, detail: str) -> None:
        nonlocal step_num
        step_num += 1
        steps.append(PlanStep(step=step_num, tool=tool, status="success", detail=detail))


    if "text" in types_present:
        add("Text Extractor", "Parse and normalize user query text.")

    if "pdf" in types_present:
        pdf_files = [s.filename for s in sources if s.source_type == "pdf"]
        fnames = ", ".join(pdf_files[:3]) + ("…" if len(pdf_files) > 3 else "")
        add("PDF Parser", f"Extract text from: {fnames}")

    if "image" in types_present:
        img_files = [s.filename for s in sources if s.source_type == "image"]
        fnames = ", ".join(img_files[:3]) + ("…" if len(img_files) > 3 else "")
        has_code = any(
            s.metadata.get("content_type") in ("code", "mixed")
            for s in sources if s.source_type == "image"
        )
        detail = f"Run EasyOCR on: {fnames}"
        if has_code:
            detail += " (code detected)"
        add("OCR Extractor", detail)

    if "audio" in types_present:
        aud_files = [s.filename for s in sources if s.source_type == "audio"]
        fnames = ", ".join(aud_files[:3]) + ("…" if len(aud_files) > 3 else "")
        add("Audio Transcriber", f"Whisper transcription: {fnames}")


    add("Context Builder", "Merge all extracted sources into unified context with semantic tags.")


    if intent == "comparison":
        add("Comparison Planner", "Identify shared topics and key differences across all sources.")
        add("LLM Execution", "Cross-source comparison with structured reasoning.")
    elif intent == "code_explanation":
        add("Code Analyst", "Identify language, explain logic, flag bugs, estimate complexity.")
        add("LLM Execution", "Detailed code analysis response.")
    elif intent == "summarize":
        add("Summarizer", "Condense all sources into key points.")
        add("LLM Execution", "Generate structured summary with bullet points.")
    elif intent == "sentiment":
        add("Sentiment Analyser", "Measure tone, polarity, and intensity across sources.")
        add("LLM Execution", "Sentiment analysis report.")
    elif intent == "question_answering":
        add("QA Retriever", "Ground answers in the provided source materials.")
        add("LLM Execution", "Precise answer citing source material.")
    elif intent == "followup":
        add("Clarification Request", "Intent ambiguous — requesting clarification from user.")
    else:
        add("LLM Execution", "Generate general-purpose response grounded in provided context.")


    add("Response Formatter", "Format and return structured response with trace.")

    return steps
