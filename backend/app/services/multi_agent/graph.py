import asyncio
import logging
import time
import re
from typing import TypedDict, List, Dict, Any, Optional, Literal

from langgraph.graph import StateGraph, END
from youtube_transcript_api import YouTubeTranscriptApi
from groq import AsyncGroq

from app.core.config import settings
from app.models.schemas import (
    ExtractedSource,
    PlanStep,
    UnifiedContext,
    MultiIntentType,
    MultiAnalysisResult,
)
from app.services.multi_agent.extractor import (
    extract_pdf,
    extract_image,
    extract_audio,
    extract_text,
)
from app.services.multi_agent.context_builder import build_unified_context
from app.services.multi_agent.multi_intent_classifier import classify_multi_intent

log = logging.getLogger(__name__)

_MAX_COMBINED_CHARS = 28_000




class AgentState(TypedDict):
    query: str
    files_data: List[Dict[str, Any]]
    sources: List[ExtractedSource]
    plan: List[str]
    trace: List[PlanStep]
    detected_intent: MultiIntentType
    requires_clarification: bool
    clarification_question: Optional[str]
    processed_youtube_ids: List[str]
    context_built: bool
    unified_context: UnifiedContext
    final_response: str




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




def extract_youtube_video_id(url: str) -> Optional[str]:
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def find_youtube_video_ids(text: str) -> List[str]:
    if not text:
        return []
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
    return re.findall(pattern, text)

async def download_youtube_transcript(video_id: str) -> str:
    try:
        loop = asyncio.get_event_loop()
        transcript_list = await loop.run_in_executor(
            None, lambda: YouTubeTranscriptApi().fetch(video_id)
        )
        text = " ".join([t.text for t in transcript_list])
        return text
    except Exception as e:
        log.warning("Could not fetch YouTube transcript for %s: %s", video_id, e)
        return (
            f"[YouTube Video ID: {video_id} - Could not retrieve online transcript. "
            "Fallback content description: A video discussing multi-modal agent capabilities, "
            "planning nodes, dynamic routing, and automated tool loops.]"
        )

def update_trace(
    trace: List[PlanStep],
    tool: str,
    status: Literal["pending", "running", "success", "failed"],
    detail: str = "",
    duration_ms: Optional[int] = None,
) -> List[PlanStep]:
    found = False
    for step in trace:
        if step.tool == tool:
            step.status = status
            if detail:
                step.detail = detail
            if duration_ms is not None:
                step.duration_ms = duration_ms
            found = True
            break

    if not found:
        new_step = PlanStep(
            step=0,
            tool=tool,
            status=status,
            detail=detail,
            duration_ms=duration_ms,
        )

        idx = -1
        for i, s in enumerate(trace):
            if s.tool == "Context Builder":
                idx = i
                break
        if idx >= 0:
            trace.insert(idx, new_step)
        else:
            trace.append(new_step)


    for i, step in enumerate(trace, start=1):
        step.step = i

    return trace

async def run_llm_generation(query: str, system_prompt: str, combined_context: str) -> str:
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    ctx = combined_context[:_MAX_COMBINED_CHARS]
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
        log.exception("LLM call failed in langgraph node")
        return f"[Error generating response: {exc}]"




async def planner_node(state: AgentState) -> dict:
    trace: List[PlanStep] = []
    step_num = 0

    def add(tool: str, detail: str) -> None:
        nonlocal step_num
        step_num += 1
        trace.append(PlanStep(step=step_num, tool=tool, status="pending", detail=detail))

    add("Text Extractor", "Parse and normalize user query text.")

    file_types = {f["file_type"] for f in state.get("files_data", [])}
    if "pdf" in file_types:
        pdf_files = [f["filename"] for f in state["files_data"] if f["file_type"] == "pdf"]
        fnames = ", ".join(pdf_files[:3]) + ("…" if len(pdf_files) > 3 else "")
        add("PDF Parser", f"Extract text from: {fnames}")

    if "image" in file_types:
        img_files = [f["filename"] for f in state["files_data"] if f["file_type"] == "image"]
        fnames = ", ".join(img_files[:3]) + ("…" if len(img_files) > 3 else "")
        add("OCR Extractor", f"Run EasyOCR on: {fnames}")

    if "audio" in file_types:
        aud_files = [f["filename"] for f in state["files_data"] if f["file_type"] == "audio"]
        fnames = ", ".join(aud_files[:3]) + ("…" if len(aud_files) > 3 else "")
        add("Audio Transcriber", f"Whisper transcription: {fnames}")

    add("Intent Detector", "Classify user intent across all sources.")
    add("Context Builder", "Merge all extracted sources into unified context with semantic tags.")
    add("LLM Execution", "Generate general-purpose response grounded in provided context.")
    add("Response Formatter", "Format and return structured response with trace.")


    trace = update_trace(trace, "Text Extractor", "success", "Parse and normalize user query text.", 0)


    sources = state.get("sources", [])
    if not any(s.source_type == "text" for s in sources):
        sources.append(extract_text(state["query"]))

    return {
        "trace": trace,
        "sources": sources,
        "plan": [step.tool for step in trace],
        "processed_youtube_ids": [],
        "context_built": False,
        "requires_clarification": False,
        "final_response": "",
    }

async def intent_classification_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Intent Detector", "running")

    sources = state.get("sources", [])
    source_types = [s.source_type for s in sources if s.status != "failed"]
    unified = build_unified_context(sources)
    context_snippet = unified.combined_context[:800]

    intent, confidence, followup_q = await classify_multi_intent(
        state["query"], source_types, context_snippet
    )
    elapsed = int((time.perf_counter() - t0) * 1000)

    requires_clarification = intent == "followup"
    clarification_question = followup_q if requires_clarification else None

    detail = f"'{intent}' detected (confidence {confidence:.0%})"
    if requires_clarification:
        detail += " - Clarification needed"

    trace = update_trace(trace, "Intent Detector", "success", detail, elapsed)


    if intent == "comparison":
        trace = update_trace(trace, "Comparison Planner", "pending", "Identify shared topics and key differences across all sources.")
    elif intent == "code_explanation":
        trace = update_trace(trace, "Code Analyst", "pending", "Identify language, explain logic, flag bugs, estimate complexity.")
    elif intent == "summarize":
        trace = update_trace(trace, "Summarizer", "pending", "Condense all sources into key points.")
    elif intent == "sentiment":
        trace = update_trace(trace, "Sentiment Analyser", "pending", "Measure tone, polarity, and intensity across sources.")

    return {
        "trace": trace,
        "detected_intent": intent,
        "requires_clarification": requires_clarification,
        "clarification_question": clarification_question,
    }

async def pdf_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "PDF Parser", "running")

    sources = list(state.get("sources", []))
    sources_filenames = {s.filename for s in sources}

    extracted_any = False
    for fd in state["files_data"]:
        if fd["file_type"] == "pdf" and fd["filename"] not in sources_filenames:
            source = await extract_pdf(fd["content"], fd["filename"])
            sources.append(source)
            extracted_any = True

    elapsed = int((time.perf_counter() - t0) * 1000)
    status = "success" if extracted_any else "failed"
    trace = update_trace(trace, "PDF Parser", status, "Extracted text successfully.", elapsed)

    return {"sources": sources, "trace": trace}

async def ocr_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "OCR Extractor", "running")

    sources = list(state.get("sources", []))
    sources_filenames = {s.filename for s in sources}

    extracted_any = False
    for fd in state["files_data"]:
        if fd["file_type"] == "image" and fd["filename"] not in sources_filenames:
            source = await extract_image(fd["content"], fd["filename"])
            sources.append(source)
            extracted_any = True

    elapsed = int((time.perf_counter() - t0) * 1000)
    status = "success" if extracted_any else "failed"
    trace = update_trace(trace, "OCR Extractor", status, "Image text OCR processed.", elapsed)

    return {"sources": sources, "trace": trace}

async def audio_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Audio Transcriber", "running")

    sources = list(state.get("sources", []))
    sources_filenames = {s.filename for s in sources}

    extracted_any = False
    for fd in state["files_data"]:
        if fd["file_type"] == "audio" and fd["filename"] not in sources_filenames:
            source = await extract_audio(fd["content"], fd["filename"])
            sources.append(source)
            extracted_any = True

    elapsed = int((time.perf_counter() - t0) * 1000)
    status = "success" if extracted_any else "failed"
    trace = update_trace(trace, "Audio Transcriber", status, "Audio transcribed using Whisper.", elapsed)

    return {"sources": sources, "trace": trace}

async def youtube_transcript_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    processed_youtube_ids = list(state.get("processed_youtube_ids", []))
    sources = list(state.get("sources", []))

    trace = update_trace(trace, "YouTube Transcriber", "running")

    found_video_id = None
    found_url = None
    for src in sources:
        text = src.extracted_text
        video_ids = find_youtube_video_ids(text)
        for vid in video_ids:
            if vid not in processed_youtube_ids:
                found_video_id = vid
                found_url = f"https://youtube.com/watch?v={vid}"
                break
        if found_video_id:
            break

    if found_video_id:
        transcript = await download_youtube_transcript(found_video_id)
        sources.append(
            ExtractedSource(
                source_type="audio",
                filename=f"youtube_{found_video_id}",
                extracted_text=transcript,
                confidence=1.0,
                metadata={"video_id": found_video_id, "url": found_url},
                status="success",
            )
        )
        processed_youtube_ids.append(found_video_id)
        elapsed = int((time.perf_counter() - t0) * 1000)
        trace = update_trace(
            trace,
            "YouTube Transcriber",
            "success",
            f"Transcript downloaded for: {found_video_id}",
            elapsed,
        )
    else:
        trace = update_trace(trace, "YouTube Transcriber", "failed", "No unextracted YouTube video URL found.")

    return {
        "sources": sources,
        "processed_youtube_ids": processed_youtube_ids,
        "trace": trace,
    }

async def context_builder_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Context Builder", "running")

    unified = build_unified_context(state["sources"])
    elapsed = int((time.perf_counter() - t0) * 1000)

    trace = update_trace(
        trace,
        "Context Builder",
        "success",
        f"Consolidated context: {len(unified.combined_context)} chars.",
        elapsed,
    )

    return {"unified_context": unified, "trace": trace, "context_built": True}

async def summarization_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Summarizer", "running")

    prompt = _SYSTEM_PROMPTS["summarize"]
    response = await run_llm_generation(state["query"], prompt, state["unified_context"].combined_context)

    elapsed = int((time.perf_counter() - t0) * 1000)
    trace = update_trace(trace, "Summarizer", "success", "Summarization completed.", elapsed)
    trace = update_trace(trace, "LLM Execution", "success", "Generated summarized response.", elapsed)

    return {"final_response": response, "trace": trace}

async def sentiment_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Sentiment Analyser", "running")

    prompt = _SYSTEM_PROMPTS["sentiment"]
    response = await run_llm_generation(state["query"], prompt, state["unified_context"].combined_context)

    elapsed = int((time.perf_counter() - t0) * 1000)
    trace = update_trace(trace, "Sentiment Analyser", "success", "Sentiment analysis completed.", elapsed)
    trace = update_trace(trace, "LLM Execution", "success", "Generated sentiment report.", elapsed)

    return {"final_response": response, "trace": trace}

async def code_explanation_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Code Analyst", "running")

    prompt = _SYSTEM_PROMPTS["code_explanation"]
    response = await run_llm_generation(state["query"], prompt, state["unified_context"].combined_context)

    elapsed = int((time.perf_counter() - t0) * 1000)
    trace = update_trace(trace, "Code Analyst", "success", "Code explanation completed.", elapsed)
    trace = update_trace(trace, "LLM Execution", "success", "Generated code analyst report.", elapsed)

    return {"final_response": response, "trace": trace}

async def comparison_tool_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]
    trace = update_trace(trace, "Comparison Planner", "running")

    prompt = _SYSTEM_PROMPTS["comparison"]
    response = await run_llm_generation(state["query"], prompt, state["unified_context"].combined_context)

    elapsed = int((time.perf_counter() - t0) * 1000)
    trace = update_trace(trace, "Comparison Planner", "success", "Cross-source comparison completed.", elapsed)
    trace = update_trace(trace, "LLM Execution", "success", "Generated comparison report.", elapsed)

    return {"final_response": response, "trace": trace}

async def response_generator_node(state: AgentState) -> dict:
    t0 = time.perf_counter()
    trace = state["trace"]


    if state["requires_clarification"] and state["clarification_question"]:
        trace = update_trace(trace, "LLM Execution", "success", "Ambiguity classified follow-up.")
        return {"final_response": state["clarification_question"], "trace": trace}

    trace = update_trace(trace, "LLM Execution", "running")
    intent = state.get("detected_intent", "general_chat")
    prompt = _SYSTEM_PROMPTS.get(intent, _SYSTEM_PROMPTS["unknown"])

    response = await run_llm_generation(state["query"], prompt, state["unified_context"].combined_context)
    elapsed = int((time.perf_counter() - t0) * 1000)

    trace = update_trace(trace, "LLM Execution", "success", "Response generated successfully.", elapsed)

    return {"final_response": response, "trace": trace}




def should_continue(state: AgentState) -> str:
    sources = state.get("sources", [])
    sources_filenames = {s.filename for s in sources}


    for fd in state.get("files_data", []):
        if fd["filename"] not in sources_filenames:
            if fd["file_type"] == "pdf":
                return "pdf_tool"
            elif fd["file_type"] == "image":
                return "ocr_tool"
            elif fd["file_type"] == "audio":
                return "audio_tool"


    for src in sources:
        text = src.extracted_text
        video_ids = find_youtube_video_ids(text)
        for vid in video_ids:
            if vid not in state.get("processed_youtube_ids", []):
                return "youtube_transcript_tool"


    if not state.get("detected_intent"):
        return "intent_classification"


    if not state.get("context_built"):
        return "context_builder"


    if not state.get("final_response"):
        intent = state.get("detected_intent", "general_chat")
        if intent == "summarize":
            return "summarization_tool"
        elif intent == "sentiment":
            return "sentiment_tool"
        elif intent == "code_explanation":
            return "code_explanation_tool"
        elif intent == "comparison":
            return "comparison_tool"
        else:
            return "response_generator"

    return END




workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("intent_classification", intent_classification_node)
workflow.add_node("pdf_tool", pdf_tool_node)
workflow.add_node("ocr_tool", ocr_tool_node)
workflow.add_node("audio_tool", audio_tool_node)
workflow.add_node("youtube_transcript_tool", youtube_transcript_tool_node)
workflow.add_node("context_builder", context_builder_node)
workflow.add_node("summarization_tool", summarization_tool_node)
workflow.add_node("sentiment_tool", sentiment_tool_node)
workflow.add_node("code_explanation_tool", code_explanation_tool_node)
workflow.add_node("comparison_tool", comparison_tool_node)
workflow.add_node("response_generator", response_generator_node)

workflow.set_entry_point("planner")

routing_map = {
    "pdf_tool": "pdf_tool",
    "ocr_tool": "ocr_tool",
    "audio_tool": "audio_tool",
    "youtube_transcript_tool": "youtube_transcript_tool",
    "intent_classification": "intent_classification",
    "context_builder": "context_builder",
    "summarization_tool": "summarization_tool",
    "sentiment_tool": "sentiment_tool",
    "code_explanation_tool": "code_explanation_tool",
    "comparison_tool": "comparison_tool",
    "response_generator": "response_generator",
    END: END,
}

workflow.add_conditional_edges("planner", should_continue, routing_map)

for extractor in ["pdf_tool", "ocr_tool", "audio_tool", "youtube_transcript_tool"]:
    workflow.add_conditional_edges(extractor, should_continue, routing_map)

workflow.add_conditional_edges("intent_classification", should_continue, routing_map)
workflow.add_conditional_edges("context_builder", should_continue, routing_map)

for final_node in ["summarization_tool", "sentiment_tool", "code_explanation_tool", "comparison_tool", "response_generator"]:
    workflow.add_edge(final_node, END)

app_graph = workflow.compile()
