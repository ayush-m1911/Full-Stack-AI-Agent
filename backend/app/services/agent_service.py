"""
Agent service — full orchestration pipeline.

Context priority: image_context > pdf_context > plain text.
All three modes preserve existing chat functionality.
"""

import json
import time
from typing import AsyncGenerator, List, Optional

from app.models.schemas import (
    ChatMessage, ChatResponse, IntentType, StreamEvent, TraceStep,
)
from app.services import pdf_context_store, image_context_store, audio_context_store
from app.services.groq_service import stream_response
from app.services.intent_classifier import classify_intent

_sessions: dict[str, list[dict]] = {}


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _trace(step: int, name: str, detail: str, status: str = "done", ms: int = 0) -> TraceStep:
    return TraceStep(step=step, name=name, status=status, detail=detail, duration_ms=ms)






async def process_chat(
    session_id: str,
    user_message: str,
    file_ids: Optional[List[str]] = None,
    pdf_id: Optional[str] = None,
    image_id: Optional[str] = None,
    audio_id: Optional[str] = None,
) -> ChatResponse:
    trace: list[TraceStep] = []
    t = time.perf_counter()
    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_message})
    trace.append(_trace(1, "Input Validation", "Message received and validated.", ms=_ms(t)))

    pdf_context: Optional[str] = None
    image_context: Optional[str] = None
    image_content_type: Optional[str] = None
    detected_language: Optional[str] = None
    audio_context: Optional[str] = None
    step = 1


    if image_id:
        step += 1
        img = image_context_store.get(image_id)
        if img and img.text:
            image_context = img.text
            image_content_type = img.content_type
            detected_language = img.detected_language
            trace.append(_trace(step, "Image Context",
                f"{img.content_type.upper()} | {len(img.text):,} chars | "
                f"conf {img.ocr_confidence:.0%}"
                + (f" | lang: {img.detected_language}" if img.detected_language else ""),
                ms=0))
        else:
            trace.append(_trace(step, "Image Context", "image_id not found.", status="error", ms=0))


    if audio_id and not image_context:
        step += 1
        aud = audio_context_store.get(audio_id)
        if aud and aud.transcript:
            audio_context = aud.transcript
            trace.append(_trace(step, "Audio Context",
                f"{aud.duration_seconds:.0f}s | {aud.word_count:,} words | lang: {aud.language or 'unknown'}",
                ms=0))
        else:
            trace.append(_trace(step, "Audio Context", "audio_id not found.", status="error", ms=0))


    if pdf_id and not image_context and not audio_context:
        step += 1
        ctx = pdf_context_store.get(pdf_id)
        if ctx and ctx.text:
            pdf_context = ctx.text
            trace.append(_trace(step, "PDF Context",
                f"{ctx.char_count:,} chars | {ctx.page_count}p | {ctx.method} | conf {ctx.confidence:.0%}",
                ms=0))
        else:
            trace.append(_trace(step, "PDF Context", "pdf_id not found.", status="error", ms=0))


    step += 1
    t = time.perf_counter()
    context_snapshot = "\n".join(f"{m['role']}: {m['content'][:120]}" for m in history[-4:])
    intent, confidence, followup_q = await classify_intent(user_message, context_snapshot)
    trace.append(_trace(step, "Intent Classification",
        f"'{intent}' (conf {confidence:.0%})", ms=_ms(t)))


    if intent in ("followup", "unknown") or confidence < 0.45:
        followup_text = followup_q or (
            "I'm not sure what you'd like me to do. Would you like me to:\n"
            "• **Summarize** the content?\n• Analyse its **Sentiment**?\n"
            "• **Answer** a specific question?\n• **Explain** a concept within it?"
        )
        step += 1
        trace.append(_trace(step, "Ambiguity Resolution", "Requesting clarification."))
        assistant_msg = ChatMessage(role="assistant", content=followup_text)
        history.append({"role": "assistant", "content": followup_text})
        return ChatResponse(
            session_id=session_id, message=assistant_msg, trace=trace,
            detected_intent="followup", needs_followup=True,
            followup_question=followup_text, extracted_text=user_message,
        )


    step += 1
    t = time.perf_counter()
    tokens: list[str] = []
    async for token in stream_response(
        user_message, intent, history[:-1],
        pdf_context=pdf_context,
        image_context=image_context,
        image_content_type=image_content_type,
        detected_language=detected_language,
        audio_context=audio_context,
    ):
        tokens.append(token)
    final_text = "".join(tokens)
    trace.append(_trace(step, "LLM Generation",
        f"Groq streamed {len(tokens)} tokens via '{intent}'.", ms=_ms(t)))

    assistant_msg = ChatMessage(role="assistant", content=final_text)
    history.append({"role": "assistant", "content": final_text})
    return ChatResponse(
        session_id=session_id, message=assistant_msg, trace=trace,
        result=final_text, extracted_text=user_message, detected_intent=intent,
    )






async def stream_chat(
    session_id: str,
    user_message: str,
    file_ids: Optional[List[str]] = None,
    pdf_id: Optional[str] = None,
    image_id: Optional[str] = None,
    audio_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:

    def emit(event: StreamEvent) -> str:
        return event.model_dump_json() + "\n"

    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_message})

    step = 1
    t = time.perf_counter()
    yield emit(StreamEvent(type="trace", trace_step=TraceStep(
        step=step, name="Input Validation", status="done",
        detail="Message received and validated.", duration_ms=_ms(t),
    )))

    pdf_context: Optional[str] = None
    image_context: Optional[str] = None
    image_content_type: Optional[str] = None
    detected_language: Optional[str] = None
    audio_context: Optional[str] = None


    if image_id:
        step += 1
        t = time.perf_counter()
        yield emit(StreamEvent(type="trace", trace_step=TraceStep(
            step=step, name="Image Context", status="running",
            detail="Loading OCR-extracted image text...",
        )))
        img = image_context_store.get(image_id)
        if img and img.text:
            image_context = img.text
            image_content_type = img.content_type
            detected_language = img.detected_language
            lang_note = f" | language: {img.detected_language}" if img.detected_language else ""
            detail = (
                f"{img.content_type.upper()} detected | "
                f"{len(img.text):,} chars | "
                f"OCR conf: {img.ocr_confidence:.0%}"
                f"{lang_note}"
            )
            yield emit(StreamEvent(type="trace", trace_step=TraceStep(
                step=step, name="Image Context", status="done",
                detail=detail, duration_ms=_ms(t),
            )))
            yield emit(StreamEvent(
                type="image_context",
                data=json.dumps({
                    "content_type": img.content_type,
                    "detected_language": img.detected_language,
                    "ocr_confidence": img.ocr_confidence,
                    "char_count": len(img.text),
                    "width": img.width,
                    "height": img.height,
                }),
            ))
        else:
            yield emit(StreamEvent(type="trace", trace_step=TraceStep(
                step=step, name="Image Context", status="error",
                detail="image_id not found — proceeding without image context.",
                duration_ms=_ms(t),
            )))


    if audio_id and not image_context:
        step += 1
        t = time.perf_counter()
        yield emit(StreamEvent(type="trace", trace_step=TraceStep(
            step=step, name="Audio Context", status="running",
            detail="Loading Whisper transcript...",
        )))
        aud = audio_context_store.get(audio_id)
        if aud and aud.transcript:
            audio_context = aud.transcript
            detail = (
                f"{aud.duration_seconds:.0f}s audio | "
                f"{aud.word_count:,} words | "
                f"lang: {aud.language or 'unknown'}"
            )
            yield emit(StreamEvent(type="trace", trace_step=TraceStep(
                step=step, name="Audio Context", status="done",
                detail=detail, duration_ms=_ms(t),
            )))
            yield emit(StreamEvent(
                type="audio_context",
                data=json.dumps({
                    "duration_seconds": aud.duration_seconds,
                    "word_count": aud.word_count,
                    "char_count": aud.char_count,
                    "language": aud.language,
                    "has_summaries": bool(aud.summaries),
                }),
            ))
        else:
            yield emit(StreamEvent(type="trace", trace_step=TraceStep(
                step=step, name="Audio Context", status="error",
                detail="audio_id not found — proceeding without audio context.",
                duration_ms=_ms(t),
            )))


    if pdf_id and not image_context and not audio_context:
        step += 1
        t = time.perf_counter()
        yield emit(StreamEvent(type="trace", trace_step=TraceStep(
            step=step, name="PDF Context", status="running",
            detail="Loading extracted PDF text...",
        )))
        ctx = pdf_context_store.get(pdf_id)
        if ctx and ctx.text:
            pdf_context = ctx.text
            detail = (
                f"Loaded {ctx.char_count:,} chars | {ctx.page_count} pages | "
                f"{ctx.method} | conf {ctx.confidence:.0%}"
            )
            yield emit(StreamEvent(type="trace", trace_step=TraceStep(
                step=step, name="PDF Context", status="done",
                detail=detail, duration_ms=_ms(t),
            )))
            yield emit(StreamEvent(
                type="pdf_context",
                data=json.dumps({
                    "method": ctx.method,
                    "confidence": ctx.confidence,
                    "page_count": ctx.page_count,
                    "char_count": ctx.char_count,
                }),
            ))
        else:
            yield emit(StreamEvent(type="trace", trace_step=TraceStep(
                step=step, name="PDF Context", status="error",
                detail="pdf_id not found — proceeding without PDF context.",
                duration_ms=_ms(t),
            )))


    step += 1
    t = time.perf_counter()
    yield emit(StreamEvent(type="trace", trace_step=TraceStep(
        step=step, name="Intent Classification", status="running",
        detail="Calling Groq intent classifier...",
    )))
    context_snapshot = "\n".join(f"{m['role']}: {m['content'][:120]}" for m in history[-4:])
    intent, confidence, followup_q = await classify_intent(user_message, context_snapshot)

    yield emit(StreamEvent(type="trace", trace_step=TraceStep(
        step=step, name="Intent Classification", status="done",
        detail=f"Detected intent: '{intent}' (confidence {confidence:.0%})",
        duration_ms=_ms(t),
    ), detected_intent=intent))
    yield emit(StreamEvent(type="intent", detected_intent=intent))


    if intent in ("followup", "unknown") or confidence < 0.45:
        followup_text = followup_q or (
            "I'm not sure what you'd like me to do. Would you like me to:\n"
            "• **Summarize** the content?\n• Analyse its **Sentiment**?\n"
            "• **Answer** a specific question?\n• **Explain** a concept within it?"
        )
        step += 1
        yield emit(StreamEvent(type="trace", trace_step=TraceStep(
            step=step, name="Ambiguity Resolution", status="done",
            detail="Intent unclear -- requesting clarification.", duration_ms=0,
        )))
        yield emit(StreamEvent(type="followup", data=followup_text))
        history.append({"role": "assistant", "content": followup_text})
        yield emit(StreamEvent(type="done"))
        return


    step += 1
    t = time.perf_counter()
    ctx_note = (
        f" with IMAGE ({image_content_type})" if image_context else
        f" with AUDIO transcript" if audio_context else
        " with PDF context" if pdf_context else ""
    )
    yield emit(StreamEvent(type="trace", trace_step=TraceStep(
        step=step, name="LLM Generation", status="running",
        detail=f"Streaming Groq [{intent}] response{ctx_note}...",
    )))

    collected: list[str] = []
    async for token in stream_response(
        user_message, intent, history[:-1],
        pdf_context=pdf_context,
        image_context=image_context,
        image_content_type=image_content_type,
        detected_language=detected_language,
        audio_context=audio_context,
    ):
        collected.append(token)
        yield emit(StreamEvent(type="token", data=token))

    final_text = "".join(collected)
    yield emit(StreamEvent(type="trace", trace_step=TraceStep(
        step=step, name="LLM Generation", status="done",
        detail=f"Generated {len(collected)} tokens.", duration_ms=_ms(t),
    )))
    history.append({"role": "assistant", "content": final_text})
    yield emit(StreamEvent(type="result", data=final_text))
    yield emit(StreamEvent(type="done"))


def get_session_history(session_id: str) -> list[dict]:
    return _sessions.get(session_id, [])
