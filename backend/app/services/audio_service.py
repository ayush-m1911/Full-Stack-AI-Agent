"""
Audio transcription service using OpenAI Whisper (local, CPU).

Pipeline:
  1. Write audio bytes to a temp file (Whisper needs a file path)
  2. Load Whisper "base" model (cached after first run ~140 MB)
  3. Transcribe → get text, language, word-level segments
  4. Compute duration from segment timestamps
  5. Generate three summary formats via Groq
  6. Return AudioTranscriptionData

Runs Whisper in a thread-pool to avoid blocking the async event loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)



WHISPER_MODEL = "base"
MAX_TRANSCRIPT_CHARS = 14_000

_whisper_model = None
_model_lock = asyncio.Lock()






@dataclass
class AudioTranscriptionData:
    transcript: str
    duration_seconds: float
    language: Optional[str]
    word_count: int
    char_count: int
    summaries: dict = field(default_factory=dict)
    warning: Optional[str] = None






def _transcribe_sync(audio_bytes: bytes, suffix: str) -> tuple[str, float, str | None]:
    """
    Write bytes to a temp file, run Whisper, return (text, duration_secs, language).
    Must run in a thread pool.
    """
    global _whisper_model
    import whisper

    if _whisper_model is None:
        log.info("Loading Whisper '%s' model (first run downloads ~140 MB)...", WHISPER_MODEL)
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        log.info("Whisper model loaded.")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = _whisper_model.transcribe(tmp_path, fp16=False, verbose=False)
        text: str = result.get("text", "").strip()
        language: str | None = result.get("language")


        segs = result.get("segments", [])
        duration = segs[-1]["end"] if segs else 0.0

        return text, float(duration), language
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass






async def _generate_summaries(transcript: str) -> dict:
    """Call Groq to produce one-line, 3-bullet, and 5-sentence summaries."""
    from groq import AsyncGroq
    from app.core.config import settings

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)


    snippet = transcript[:10_000]

    prompt = (
        "You are a professional summarizer. Given the following audio transcript, "
        "generate EXACTLY three types of summaries:\n\n"
        "1. ONE_LINE: A single sentence (max 25 words) capturing the core message.\n"
        "2. BULLETS: Exactly 3 concise bullet points (use '•' prefix, one per line).\n"
        "3. PARAGRAPH: Exactly 5 complete sentences as a coherent paragraph.\n\n"
        "Format your response EXACTLY like this (keep the labels):\n"
        "ONE_LINE: <your one-line summary>\n"
        "BULLETS:\n"
        "• <point 1>\n"
        "• <point 2>\n"
        "• <point 3>\n"
        "PARAGRAPH: <your 5-sentence paragraph>\n\n"
        f"TRANSCRIPT:\n{snippet}"
    )

    resp = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600,
    )

    raw = resp.choices[0].message.content or ""
    return _parse_summaries(raw)


def _parse_summaries(raw: str) -> dict:
    """Parse structured summary response into dict."""
    one_line = ""
    bullets: list[str] = []
    paragraph = ""

    lines = raw.splitlines()
    section = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("ONE_LINE:"):
            one_line = stripped[len("ONE_LINE:"):].strip()
            section = "one_line"
        elif stripped.startswith("BULLETS:"):
            section = "bullets"
        elif stripped.startswith("PARAGRAPH:"):
            paragraph = stripped[len("PARAGRAPH:"):].strip()
            section = "paragraph"
        elif section == "bullets" and stripped.startswith("•"):
            bullets.append(stripped[1:].strip())
        elif section == "paragraph" and stripped and not stripped.startswith("ONE_LINE") and not stripped.startswith("BULLETS"):
            if paragraph:
                paragraph += " " + stripped
            else:
                paragraph = stripped


    bullets = bullets[:3]

    return {
        "one_line": one_line or "Summary not available.",
        "bullets": bullets or ["No bullet points generated."],
        "paragraph": paragraph or "Paragraph summary not available.",
    }






async def transcribe_audio(audio_bytes: bytes, filename: str = "audio") -> AudioTranscriptionData:
    """
    Full pipeline — always returns AudioTranscriptionData, never raises.
    """
    suffix = ".wav"
    name_lower = filename.lower()
    if name_lower.endswith(".mp3"):
        suffix = ".mp3"
    elif name_lower.endswith(".m4a"):
        suffix = ".m4a"
    elif name_lower.endswith(".ogg"):
        suffix = ".ogg"
    elif name_lower.endswith(".flac"):
        suffix = ".flac"


    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as pool:
            text, duration, language = await loop.run_in_executor(
                pool, _transcribe_sync, audio_bytes, suffix
            )
    except Exception as exc:
        log.exception("Whisper transcription failed for '%s'", filename)
        return AudioTranscriptionData(
            transcript="",
            duration_seconds=0.0,
            language=None,
            word_count=0,
            char_count=0,
            summaries={},
            warning=f"Transcription failed: {exc}. Ensure FFmpeg is installed and on PATH.",
        )

    if not text:
        return AudioTranscriptionData(
            transcript="",
            duration_seconds=duration,
            language=language,
            word_count=0,
            char_count=0,
            summaries={},
            warning="Whisper returned empty transcript. The audio may be silent or unsupported.",
        )


    truncation_warning = None
    if len(text) > MAX_TRANSCRIPT_CHARS:
        text = text[:MAX_TRANSCRIPT_CHARS]
        truncation_warning = f"Transcript truncated to {MAX_TRANSCRIPT_CHARS:,} characters."


    try:
        summaries = await _generate_summaries(text)
    except Exception as exc:
        log.warning("Summary generation failed: %s", exc)
        summaries = {
            "one_line": "Summary unavailable.",
            "bullets": ["Summary generation failed."],
            "paragraph": "Summary generation failed.",
        }

    return AudioTranscriptionData(
        transcript=text,
        duration_seconds=round(duration, 2),
        language=language,
        word_count=len(text.split()),
        char_count=len(text),
        summaries=summaries,
        warning=truncation_warning,
    )
