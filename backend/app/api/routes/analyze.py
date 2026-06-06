"""
POST /api/v1/analyze

Accepts a multipart/form-data request with:
  - query (str, required form field)
  - files (one or more UploadFile — any mix of PDF / PNG / JPG / MP3 / WAV / M4A)

Returns MultiAnalysisResponse containing:
  - extracted_sources  — per-file extraction results
  - unified_context    — merged LLM context
  - detected_intent    — classified intent
  - requires_clarification / clarification_question
  - plan_trace         — execution plan steps
  - result             — LLM-generated response text
"""

import asyncio
import logging
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.schemas import ExtractedSource, MultiAnalysisResponse, MultiAnalysisResult
from app.services.multi_agent.extractor import (
    extract_audio,
    extract_image,
    extract_pdf,
    extract_text,
)
from app.services.multi_agent.pipeline import run_pipeline

log = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Multi-Input Agent"])


_PDF_TYPES   = {"application/pdf"}
_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mp4", "audio/m4a", "audio/x-m4a", "audio/ogg", "audio/flac",
    "audio/x-flac",
}

_PDF_EXT   = (".pdf",)
_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
_AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac")

MAX_FILE_MB = 100


def _detect_type(file: UploadFile) -> str | None:
    """Return 'pdf' | 'image' | 'audio' | None based on MIME + extension."""
    ct = (file.content_type or "").lower().strip()
    name = (file.filename or "").lower()

    if ct in _PDF_TYPES or any(name.endswith(e) for e in _PDF_EXT):
        return "pdf"
    if ct in _IMAGE_TYPES or any(name.endswith(e) for e in _IMAGE_EXT):
        return "image"
    if ct in _AUDIO_TYPES or any(name.endswith(e) for e in _AUDIO_EXT):
        return "audio"
    return None


@router.post(
    "",
    response_model=MultiAnalysisResponse,
    summary="Unified multi-modal analysis (text + PDF + image + audio)",
)
async def analyze(
    query: str = Form(..., min_length=1, max_length=32_000, description="User query / instruction"),
    files: List[UploadFile] = File(default=[], description="Any mix of PDF, PNG/JPG, MP3/WAV/M4A"),
) -> MultiAnalysisResponse:
    """
    Single endpoint for multi-modal analysis.

    - Accepts any combination of file types in one request.
    - Processes each file in parallel using asyncio.gather.
    - Failures are isolated per file (one bad PDF never blocks audio transcription).
    - Returns structured trace, extracted content, intent, and LLM response.
    """


    files_data = []
    sources: list[ExtractedSource] = []

    for f in files:
        file_type = _detect_type(f)
        if file_type is None:
            log.warning("Skipping unsupported file: %s (%s)", f.filename, f.content_type)
            sources.append(ExtractedSource(
                source_type="text",
                filename=f.filename or "unknown",
                extracted_text="",
                confidence=0.0,
                metadata={"content_type": f.content_type},
                warning=f"Unsupported file type: {f.content_type}",
                status="failed",
            ))
            continue

        content = await f.read()
        if len(content) > MAX_FILE_MB * 1024 * 1024:
            sources.append(ExtractedSource(
                source_type=file_type or "text",
                filename=f.filename or "unknown",
                extracted_text="",
                confidence=0.0,
                metadata={},
                warning=f"File exceeds {MAX_FILE_MB} MB limit.",
                status="failed",
            ))
            continue

        fname = f.filename or f"file.{file_type}"
        files_data.append({
            "filename": fname,
            "content": content,
            "file_type": file_type
        })


    result: MultiAnalysisResult = await run_pipeline(query, sources=sources, files_data=files_data)

    return MultiAnalysisResponse(data=result)
