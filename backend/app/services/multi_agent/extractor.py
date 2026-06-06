"""
Extraction layer — delegates to existing per-type services.

Each function accepts raw bytes + filename and returns an ExtractedSource.
Failures are isolated: one bad file never blocks the others.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from app.models.schemas import ExtractedSource

log = logging.getLogger(__name__)






async def extract_pdf(content: bytes, filename: str) -> ExtractedSource:
    """Delegate to pdf_service.extract_pdf_text."""
    t0 = time.perf_counter()
    try:
        from app.services.pdf_service import extract_pdf_text
        result = await extract_pdf_text(content, filename)
        elapsed = int((time.perf_counter() - t0) * 1000)

        if result.method == "failed" or not result.text:
            return ExtractedSource(
                source_type="pdf",
                filename=filename,
                extracted_text="",
                confidence=0.0,
                metadata={"method": result.method, "duration_ms": elapsed},
                warning=result.warning or "No text extracted from PDF.",
                status="empty" if result.method != "failed" else "failed",
            )

        return ExtractedSource(
            source_type="pdf",
            filename=filename,
            extracted_text=result.text,
            confidence=result.confidence,
            metadata={
                "method": result.method,
                "page_count": result.page_count,
                "char_count": result.char_count,
                "duration_ms": elapsed,
            },
            warning=result.warning,
            status="success",
        )
    except Exception as exc:
        log.exception("PDF extraction failed for '%s'", filename)
        return ExtractedSource(
            source_type="pdf",
            filename=filename,
            extracted_text="",
            confidence=0.0,
            metadata={},
            warning=f"PDF extraction error: {exc}",
            status="failed",
        )






async def extract_image(content: bytes, filename: str) -> ExtractedSource:
    """Delegate to image_service.extract_image_text."""
    t0 = time.perf_counter()
    try:
        from app.services.image_service import extract_image_text
        result = await extract_image_text(content, filename)
        elapsed = int((time.perf_counter() - t0) * 1000)

        if result.content_type == "empty" or not result.text:
            return ExtractedSource(
                source_type="image",
                filename=filename,
                extracted_text="",
                confidence=0.0,
                metadata={"content_type": result.content_type, "duration_ms": elapsed},
                warning=result.warning or "No text found in image.",
                status="empty",
            )

        return ExtractedSource(
            source_type="image",
            filename=filename,
            extracted_text=result.text,
            confidence=result.ocr_confidence,
            metadata={
                "content_type": result.content_type,
                "detected_language": result.detected_language,
                "width": result.width,
                "height": result.height,
                "char_count": len(result.text),
                "duration_ms": elapsed,
            },
            warning=result.warning,
            status="success",
        )
    except Exception as exc:
        log.exception("Image extraction failed for '%s'", filename)
        return ExtractedSource(
            source_type="image",
            filename=filename,
            extracted_text="",
            confidence=0.0,
            metadata={},
            warning=f"Image OCR error: {exc}",
            status="failed",
        )






async def extract_audio(content: bytes, filename: str) -> ExtractedSource:
    """Delegate to audio_service.transcribe_audio (transcript only, no summaries)."""
    t0 = time.perf_counter()
    try:
        from app.services.audio_service import transcribe_audio
        result = await transcribe_audio(content, filename)
        elapsed = int((time.perf_counter() - t0) * 1000)

        if not result.transcript:
            return ExtractedSource(
                source_type="audio",
                filename=filename,
                extracted_text="",
                confidence=0.0,
                metadata={"duration_seconds": result.duration_seconds, "duration_ms": elapsed},
                warning=result.warning or "Empty transcript.",
                status="empty",
            )

        return ExtractedSource(
            source_type="audio",
            filename=filename,
            extracted_text=result.transcript,
            confidence=1.0,
            metadata={
                "duration_seconds": result.duration_seconds,
                "language": result.language,
                "word_count": result.word_count,
                "char_count": result.char_count,
                "duration_ms": elapsed,
            },
            warning=result.warning,
            status="success",
        )
    except Exception as exc:
        log.exception("Audio extraction failed for '%s'", filename)
        return ExtractedSource(
            source_type="audio",
            filename=filename,
            extracted_text="",
            confidence=0.0,
            metadata={},
            warning=f"Audio transcription error: {exc}",
            status="failed",
        )






def extract_text(text: str) -> ExtractedSource:
    """Wrap the user's plain-text query as an ExtractedSource."""
    return ExtractedSource(
        source_type="text",
        filename="query",
        extracted_text=text.strip(),
        confidence=1.0,
        metadata={"char_count": len(text)},
        status="success",
    )
