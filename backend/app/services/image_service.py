"""
Image OCR service using EasyOCR.

Pipeline:
  1. Load image with Pillow (validate, resize if huge)
  2. Run EasyOCR for text extraction with word-level confidence
  3. Classify content: code vs plain text vs mixed
  4. Detect programming language if code is found
  5. Return structured ImageExtractionResult

EasyOCR downloads model weights on first run (~100 MB, cached in ~/.EasyOCR).
No external binary required — pure Python.
"""

from __future__ import annotations

import asyncio
import io
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


MAX_DIM = 4096

_reader = None
_reader_lock = asyncio.Lock()


MAX_CONTEXT_CHARS = 12_000






_CODE_PATTERNS = [
    r'\bdef\s+\w+\s*\(',
    r'\bclass\s+\w+[\s:(]',
    r'\bimport\s+\w+',
    r'\bfrom\s+\w+\s+import\b',
    r'\bfunction\s+\w+\s*\(',
    r'\bconst\s+\w+\s*=',
    r'\blet\s+\w+\s*=',
    r'\bvar\s+\w+\s*=',
    r'\bpublic\s+\w+\s+\w+\s*\(',
    r'\bvoid\s+\w+\s*\(',
    r'\bint\s+main\s*\(',
    r'#include\s*<',
    r'\bif\s*\(.+\)\s*[{:]',
    r'\bfor\s*\(.+\)\s*\{',
    r'\bwhile\s*\(.+\)\s*\{',
    r'=>\s*\{',
    r'^\s*[{}\[\]]\s*$',
    r'//.*$',
    r'/\*.*\*/',
    r'^\s*#\s+\w',
    r';\s*$',
    r'<[a-zA-Z][^>]*>',
    r'SELECT\s+.+\s+FROM\b',
    r'\bCREATE\s+TABLE\b',
]
_CODE_RE = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in _CODE_PATTERNS]


_LANG_SIGNATURES: dict[str, list[str]] = {
    "python":     ["def ", "import ", "elif ", "print(", "::", "__init__", "lambda "],
    "javascript": ["const ", "let ", "var ", "=>", "console.log", "function ", "require(", "module.exports"],
    "typescript": ["interface ", ": string", ": number", ": boolean", "type ", "<T>", "readonly "],
    "java":       ["public class", "public static void", "System.out", "new ", "import java"],
    "csharp":     ["using System", "namespace ", "public class", "Console.Write", "var ", "=>"],
    "cpp":        ["#include", "std::", "cout <<", "int main(", "void ", "->"],
    "c":          ["#include <stdio", "printf(", "scanf(", "int main(", "malloc(", "->"],
    "go":         ["func ", "package ", "import (", "fmt.Print", ":= ", "goroutine"],
    "rust":       ["fn ", "let mut", "println!", "use std", "impl ", "pub fn"],
    "sql":        ["SELECT ", "FROM ", "WHERE ", "INSERT INTO", "CREATE TABLE", "JOIN "],
    "html":       ["<html", "<div", "<span", "<!DOCTYPE", "<body", "<head"],
    "css":        ["{", "margin:", "padding:", "color:", "font-size:", "@media"],
    "bash":       ["#!/bin/bash", "echo ", "$1", "fi\n", "then\n", "grep ", "awk "],
}


def _detect_code_and_language(text: str) -> tuple[bool, Optional[str]]:
    """Returns (is_code, language_name | None)."""
    if not text.strip():
        return False, None


    hits = sum(1 for pattern in _CODE_RE if pattern.search(text))
    is_code = hits >= 3

    if not is_code:
        return False, None


    scores: dict[str, int] = {}
    lower = text.lower()
    for lang, sigs in _LANG_SIGNATURES.items():
        scores[lang] = sum(1 for s in sigs if s.lower() in lower)

    best_lang = max(scores, key=lambda k: scores[k]) if scores else None
    if best_lang and scores[best_lang] >= 2:
        return True, best_lang

    return True, None


def _classify_content(text: str, is_code: bool) -> str:
    """Return 'code' | 'text' | 'mixed' | 'empty'."""
    if not text.strip():
        return "empty"
    if is_code:

        lines = text.splitlines()
        code_lines = sum(1 for p in _CODE_RE for l in lines if p.search(l))
        ratio = code_lines / max(len(lines), 1)
        return "code" if ratio > 0.4 else "mixed"
    return "text"






def _ocr_sync(img_bytes: bytes) -> tuple[str, float, int, int]:
    """
    Run EasyOCR on the image.
    Returns (text, avg_confidence_0_1, width_px, height_px).
    """
    global _reader

    from PIL import Image

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = img.size


    if max(w, h) > MAX_DIM:
        scale = MAX_DIM / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        w, h = img.size


    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    raw = buf.read()

    import numpy as np
    import easyocr

    if _reader is None:
        log.info("Initialising EasyOCR reader (first-time download may take a moment)...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    results = _reader.readtext(raw, detail=1, paragraph=False)


    if not results:
        return "", 0.0, w, h

    lines: list[str] = []
    confidences: list[float] = []
    for _, text, conf in results:
        if text.strip():
            lines.append(text)
            confidences.append(float(conf))

    full_text = "\n".join(lines)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return full_text, avg_conf, w, h






@dataclass
class ImageExtractionData:
    text: str
    ocr_confidence: float
    content_type: str
    detected_language: Optional[str]
    width: int
    height: int
    warning: Optional[str] = None






async def get_reader():
    """Lazy-init EasyOCR reader in thread pool (avoids blocking event loop)."""
    global _reader
    async with _reader_lock:
        if _reader is None:
            import easyocr
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as pool:
                _reader = await loop.run_in_executor(
                    pool,
                    lambda: easyocr.Reader(["en"], gpu=False, verbose=False),
                )
    return _reader


async def extract_image_text(img_bytes: bytes, filename: str = "image.png") -> ImageExtractionData:
    """
    Full pipeline — always returns ImageExtractionData, never raises.
    """

    try:
        await get_reader()
    except Exception as exc:
        return ImageExtractionData(
            text="", ocr_confidence=0.0,
            content_type="empty", detected_language=None,
            width=0, height=0,
            warning=f"EasyOCR init failed: {exc}",
        )

    loop = asyncio.get_event_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            text, conf, w, h = await loop.run_in_executor(pool, _ocr_sync, img_bytes)
    except Exception as exc:
        log.exception("EasyOCR failed for '%s'", filename)
        return ImageExtractionData(
            text="", ocr_confidence=0.0,
            content_type="empty", detected_language=None,
            width=0, height=0,
            warning=f"OCR error: {exc}",
        )


    truncation_warning = None
    if len(text) > MAX_CONTEXT_CHARS:
        text = text[:MAX_CONTEXT_CHARS]
        truncation_warning = f"Text truncated to {MAX_CONTEXT_CHARS:,} characters."

    is_code, lang = _detect_code_and_language(text)
    content_type = _classify_content(text, is_code)

    return ImageExtractionData(
        text=text,
        ocr_confidence=round(conf, 3),
        content_type=content_type,
        detected_language=lang,
        width=w,
        height=h,
        warning=truncation_warning,
    )
