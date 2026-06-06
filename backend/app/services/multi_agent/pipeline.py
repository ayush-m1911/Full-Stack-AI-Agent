"""
Multi-Input Agent Pipeline (Execution Layer).

Orchestrates:
  1. Input Analyzer  — determine what types of files were supplied
  2. Extraction Layer — run appropriate extractor per file
  3. Context Builder  — merge into UnifiedContext
  4. Intent Detection — classify user intent across all sources
  5. Planning Layer   — build step-by-step plan
  6. LLM Execution    — call Groq with unified context + system prompt
  7. Response Formatter — assemble MultiAnalysisResult

All steps run in-process; individual file failures are isolated.
"""

from __future__ import annotations

import asyncio
import logging
import time
import re
from typing import Optional

from groq import AsyncGroq

from app.core.config import settings
from app.models.schemas import (
    ExtractedSource,
    MultiAnalysisResult,
    MultiIntentType,
    PlanStep,
    UnifiedContext,
)
from app.services.multi_agent.context_builder import build_unified_context
from app.services.multi_agent.multi_intent_classifier import classify_multi_intent
from app.services.multi_agent.planner import build_plan
from app.services.multi_agent.extractor import (
    extract_pdf,
    extract_image,
    extract_audio,
    extract_text,
)

log = logging.getLogger(__name__)


_MAX_COMBINED_CHARS = 28_000





_SYSTEM_PROMPTS: dict[str, str] = {
    "summarize": (
        "You are an expert summarizer. The user has provided one or more sources "
        "(documents, images, audio transcripts). "
        "Each source is wrapped in semantic tags inside the user message. "
        "Produce a clear, structured summary covering ALL sources. "
        "Format: 1-2 sentence overview, then bullet-point key takeaways per source."
    ),
    "sentiment": (
        "You are a sentiment analysis expert. Analyse emotional tone, polarity "
        "(positive / negative / neutral / mixed), and intensity across ALL provided sources. "
        "Report sentiment per source and an overall combined sentiment."
    ),
    "question_answering": (
        "You are a precise Q&A assistant. Answer the user's question using ONLY the "
        "provided source material. Cite the specific source (document name, image, or transcript) "
        "that supports each part of your answer. If the answer is not in the sources, say so clearly."
    ),
    "code_explanation": (
        "You are an expert code analyst. Source material may include code extracted from images via OCR. "
        "For each code snippet:\n"
        "1. **Language** — identify programming language.\n"
        "2. **Logic** — explain what the code does step by step.\n"
        "3. **Bugs** — identify potential bugs, edge cases, or issues.\n"
        "4. **Complexity** — estimate time and space complexity (Big-O) where relevant.\n"
        "5. **Improvements** — suggest any obvious optimisations.\n"
        "Use code blocks and headings for clarity."
    ),
    "comparison": (
        "You are a comparative analyst. The user has provided MULTIPLE sources "
        "(documents, images, audio recordings). "
        "Your task is to compare and contrast them:\n"
        "1. **Shared themes** — what topics or ideas do they have in common?\n"
        "2. **Key differences** — where do they diverge?\n"
        "3. **Overall assessment** — do they address the same topic? Summarise the relationship.\n"
        "Structure your response with clear headings for each section."
    ),
    "general_chat": (
        "You are a helpful AI assistant. The user may have attached documents, images, or audio. "
        "Use the provided content as context to answer helpfully. "
        "If no source material is relevant, respond conversationally."
    ),
    "followup": (
        "You are a helpful AI assistant. Ask the user exactly one clear, friendly clarifying question "
        "to understand what they would like to do with the provided content."
    ),
    "unknown": (
        "You are a helpful AI assistant. Do your best to address the user's request "
        "using the provided source material."
    ),
}






async def _call_llm(
    query: str,
    intent: MultiIntentType,
    unified_context: UnifiedContext,
    clarification_question: Optional[str] = None,
) -> str:
    """Call Groq with the unified context and return the response string."""
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    system_prompt = _SYSTEM_PROMPTS.get(intent, _SYSTEM_PROMPTS["unknown"])


    if intent == "followup" and clarification_question:
        return clarification_question


    ctx = unified_context.combined_context[:_MAX_COMBINED_CHARS]
    if ctx:
        user_content = f"{ctx}\n\n[USER QUERY]\n{query}"
    else:
        user_content = query

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        log.exception("LLM call failed in multi-agent pipeline")
        return f"[Error generating response: {exc}]"






async def run_pipeline(
    query: str,
    sources: list[ExtractedSource] = [],
    files_data: list[dict] = [],
) -> MultiAnalysisResult:
    """
    Unified extraction and URL analysis pipeline.
    Runs sequential file extractions, robust URL extraction, webpage/YouTube fetching,
    builds unified context, classifies intent, and generates grounded LLM response.
    """
    extracted_sources = list(sources)
    plan_trace: list[PlanStep] = []
    step_num = 0

    def add_trace(tool: str, status: str, detail: str = "", duration_ms: int = 0):
        nonlocal step_num
        step_num += 1
        plan_trace.append(PlanStep(
            step=step_num,
            tool=tool,
            status=status,
            detail=detail,
            duration_ms=duration_ms
        ))


    if not any(s.source_type == "text" for s in extracted_sources):
        extracted_sources.append(extract_text(query))


    pdf_files = [f for f in files_data if f["file_type"] == "pdf"]
    if pdf_files:
        t0 = time.perf_counter()
        pdf_details = []
        for f in pdf_files:
            try:
                source = await extract_pdf(f["content"], f["filename"])
                extracted_sources.append(source)
                pdf_details.append(f"{f['filename']} ({source.status})")
            except Exception as e:
                pdf_details.append(f"{f['filename']} (error: {e})")
        elapsed = int((time.perf_counter() - t0) * 1000)
        add_trace("PDF Extraction", "success", f"Processed: {', '.join(pdf_details)}", elapsed)


    img_files = [f for f in files_data if f["file_type"] == "image"]
    if img_files:
        t0 = time.perf_counter()
        img_details = []
        for f in img_files:
            try:
                source = await extract_image(f["content"], f["filename"])
                extracted_sources.append(source)
                img_details.append(f"{f['filename']} ({source.status})")
            except Exception as e:
                img_details.append(f"{f['filename']} (error: {e})")
        elapsed = int((time.perf_counter() - t0) * 1000)
        add_trace("OCR", "success", f"Processed: {', '.join(img_details)}", elapsed)


    aud_files = [f for f in files_data if f["file_type"] == "audio"]
    if aud_files:
        t0 = time.perf_counter()
        aud_details = []
        for f in aud_files:
            try:
                source = await extract_audio(f["content"], f["filename"])
                extracted_sources.append(source)
                aud_details.append(f"{f['filename']} ({source.status})")
            except Exception as e:
                aud_details.append(f"{f['filename']} (error: {e})")
        elapsed = int((time.perf_counter() - t0) * 1000)
        add_trace("Audio Transcription", "success", f"Processed: {', '.join(aud_details)}", elapsed)


    t0 = time.perf_counter()
    all_texts = [query]
    for src in extracted_sources:
        if src.status == "success" and src.extracted_text:
            all_texts.append(src.extracted_text)
    combined_text_for_urls = "\n\n".join(all_texts)
    

    urls_detected = []
    raw_urls = re.findall(r'(https?://[^\s]+)', combined_text_for_urls)
    for url in raw_urls:
        url = url.rstrip('.,?!;:"\'()[]{}<>')
        if url not in urls_detected:
            urls_detected.append(url)
            
    elapsed = int((time.perf_counter() - t0) * 1000)
    add_trace("URL Detection", "success", f"Found {len(urls_detected)} URLs", elapsed)


    from app.services.multi_agent.youtube_transcript_service import YouTubeTranscriptService
    from app.services.multi_agent.url_fetcher import URLFetcher

    youtube_urls = []
    normal_urls = []
    for url in urls_detected:
        if YouTubeTranscriptService.extract_video_id(url) is not None:
            youtube_urls.append(url)
        else:
            normal_urls.append(url)


    if youtube_urls:
        t0 = time.perf_counter()
        for url in youtube_urls:
            video_id = YouTubeTranscriptService.extract_video_id(url)
            if video_id:
                try:
                    transcript = await YouTubeTranscriptService.fetch_transcript(video_id)
                    status = "success" if not transcript.startswith("[YouTube Video ID") else "failed"
                    extracted_sources.append(ExtractedSource(
                        source_type="url",
                        filename=f"youtube_{video_id}",
                        extracted_text=transcript,
                        confidence=1.0,
                        metadata={"url": url, "video_id": video_id, "title": f"YouTube Video {video_id}"},
                        status=status
                    ))
                except Exception as e:
                    log.warning("YouTube transcript fetch error: %s", e)
        elapsed = int((time.perf_counter() - t0) * 1000)
        add_trace("YouTube Transcript", "success", f"Processed {len(youtube_urls)} YouTube video transcripts", elapsed)


    if normal_urls:
        t0 = time.perf_counter()
        for url in normal_urls:
            try:
                res = await URLFetcher.fetch(url)
                status = "success" if not res["title"].startswith("Failed") else "failed"
                extracted_sources.append(ExtractedSource(
                    source_type="url",
                    filename=url,
                    extracted_text=res["extracted_content"],
                    confidence=1.0,
                    metadata={"url": url, "title": res["title"]},
                    status=status
                ))
            except Exception as e:
                log.warning("Web page fetch error: %s", e)
        elapsed = int((time.perf_counter() - t0) * 1000)
        add_trace("Web Fetch", "success", f"Processed {len(normal_urls)} web pages", elapsed)


    t0 = time.perf_counter()
    unified_context = build_unified_context(extracted_sources)
    elapsed = int((time.perf_counter() - t0) * 1000)
    add_trace("Context Builder", "success", f"Combined context: {len(unified_context.combined_context)} chars", elapsed)


    source_types = [s.source_type for s in extracted_sources if s.status != "failed"]
    context_snippet = unified_context.combined_context[:800]
    intent, confidence, followup_q = await classify_multi_intent(
        query, source_types, context_snippet
    )


    result_text = await _call_llm(
        query=query,
        intent=intent,
        unified_context=unified_context,
        clarification_question=followup_q if intent == "followup" else None
    )

    return MultiAnalysisResult(
        extracted_sources=extracted_sources,
        unified_context=unified_context,
        detected_intent=intent,
        requires_clarification=(intent == "followup"),
        clarification_question=followup_q if intent == "followup" else None,
        plan_trace=plan_trace,
        urls_detected=urls_detected,
        combined_context=unified_context.combined_context,
        result=result_text
    )
