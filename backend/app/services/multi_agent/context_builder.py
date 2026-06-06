"""
Unified Context Builder.

Combines all ExtractedSource objects into a single LLM-ready context blob.
Each source is wrapped in semantic XML-style tags so the LLM can distinguish
between documents, images, and audio transcripts.
"""

from __future__ import annotations

from typing import List

from app.models.schemas import ExtractedSource, UnifiedContext



_MAX_CHARS_PER_SOURCE = 10_000


def build_unified_context(sources: List[ExtractedSource]) -> UnifiedContext:
    """
    Merge all successfully extracted sources into UnifiedContext.

    combined_context layout:
      [TEXT_QUERY]
      <user query>
      [/TEXT_QUERY]

      [DOCUMENT: filename.pdf]
      <pdf text>
      [/DOCUMENT]

      [IMAGE: photo.png | CODE: python]
      <ocr text>
      [/IMAGE]

      [TRANSCRIPT: recording.mp3]
      <transcript>
      [/TRANSCRIPT]

      [URL: http://example.com/article | Title: My Article]
      <extracted web content>
      [/URL]
    """
    text_inputs: list[str] = []
    image_texts: list[str] = []
    pdf_texts: list[str] = []
    audio_transcripts: list[str] = []
    url_texts: list[str] = []
    blocks: list[str] = []

    for src in sources:
        if src.status == "failed" or not src.extracted_text.strip():
            continue

        snippet = src.extracted_text[:_MAX_CHARS_PER_SOURCE]

        if src.source_type == "text":
            text_inputs.append(snippet)
            blocks.append(f"[TEXT_QUERY]\n{snippet}\n[/TEXT_QUERY]")

        elif src.source_type == "pdf":
            pdf_texts.append(snippet)
            blocks.append(f"[DOCUMENT: {src.filename}]\n{snippet}\n[/DOCUMENT]")

        elif src.source_type == "image":
            image_texts.append(snippet)
            ct = src.metadata.get("content_type", "text")
            lang = src.metadata.get("detected_language")
            label = f"IMAGE: {src.filename}"
            if ct in ("code", "mixed") and lang:
                label += f" | CODE: {lang}"
            elif ct == "code":
                label += " | CODE"
            blocks.append(f"[{label}]\n{snippet}\n[/IMAGE: {src.filename}]")

        elif src.source_type == "audio":
            audio_transcripts.append(snippet)
            dur = src.metadata.get("duration_seconds", 0)
            lang = src.metadata.get("language") or "unknown"
            blocks.append(
                f"[TRANSCRIPT: {src.filename} | {dur:.0f}s | lang={lang}]\n"
                f"{snippet}\n"
                f"[/TRANSCRIPT]"
            )

        elif src.source_type == "url":
            url_texts.append(snippet)
            url = src.metadata.get("url") or src.filename
            title = src.metadata.get("title") or "Webpage"
            if "youtube" in src.filename.lower() or "youtube" in url.lower():
                blocks.append(f"[YOUTUBE_TRANSCRIPT: {src.filename} | URL: {url}]\n{snippet}\n[/YOUTUBE_TRANSCRIPT]")
            else:
                blocks.append(f"[URL: {url} | Title: {title}]\n{snippet}\n[/URL]")

    pdf_combined = "\n\n".join(pdf_texts)
    image_combined = "\n\n".join(image_texts)
    audio_combined = "\n\n".join(audio_transcripts)
    url_combined = "\n\n".join(url_texts)

    return UnifiedContext(
        text_inputs="\n\n".join(text_inputs),
        image_text=image_combined,
        pdf_text=pdf_combined,
        audio_transcript=audio_combined,
        pdf_content=pdf_combined,
        image_content=image_combined,
        audio_content=audio_combined,
        url_content=url_combined,
        combined_context="\n\n".join(blocks),
    )
