"""
Audio transcription service using Groq Whisper API.

Pipeline:
  1. Write audio bytes to a temporary file
  2. Send audio to Groq Whisper API
  3. Extract transcript text
  4. Generate summaries using Groq LLM
  5. Return AudioTranscriptionData
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

MAX_TRANSCRIPT_CHARS = 14_000


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
    from groq import Groq
    from app.core.config import settings

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )

        text = getattr(transcript, "text", "").strip()

        language = getattr(transcript, "language", None)

        duration = 0.0

        return text, duration, language

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def _generate_summaries(transcript: str) -> dict:
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
        "Format your response EXACTLY like this:\n"
        "ONE_LINE: <summary>\n"
        "BULLETS:\n"
        "• <point 1>\n"
        "• <point 2>\n"
        "• <point 3>\n"
        "PARAGRAPH: <paragraph>\n\n"
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

        elif (
            section == "paragraph"
            and stripped
            and not stripped.startswith("ONE_LINE")
            and not stripped.startswith("BULLETS")
        ):
            paragraph = f"{paragraph} {stripped}".strip()

    bullets = bullets[:3]

    return {
        "one_line": one_line or "Summary not available.",
        "bullets": bullets or ["No bullet points generated."],
        "paragraph": paragraph or "Paragraph summary not available.",
    }


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio",
) -> AudioTranscriptionData:

    suffix = ".wav"

    lower = filename.lower()

    if lower.endswith(".mp3"):
        suffix = ".mp3"
    elif lower.endswith(".m4a"):
        suffix = ".m4a"
    elif lower.endswith(".ogg"):
        suffix = ".ogg"
    elif lower.endswith(".flac"):
        suffix = ".flac"

    try:
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=1) as pool:
            text, duration, language = await loop.run_in_executor(
                pool,
                _transcribe_sync,
                audio_bytes,
                suffix,
            )

    except Exception as exc:
        log.exception(
            "Audio transcription failed for '%s'",
            filename,
        )

        return AudioTranscriptionData(
            transcript="",
            duration_seconds=0.0,
            language=None,
            word_count=0,
            char_count=0,
            summaries={},
            warning=f"Transcription failed: {exc}",
        )

    if not text:
        return AudioTranscriptionData(
            transcript="",
            duration_seconds=duration,
            language=language,
            word_count=0,
            char_count=0,
            summaries={},
            warning="Transcription returned empty transcript. The audio may be silent or unsupported.",
        )

    truncation_warning = None

    if len(text) > MAX_TRANSCRIPT_CHARS:
        text = text[:MAX_TRANSCRIPT_CHARS]
        truncation_warning = (
            f"Transcript truncated to {MAX_TRANSCRIPT_CHARS:,} characters."
        )

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