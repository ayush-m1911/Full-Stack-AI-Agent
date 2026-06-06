"""
PDF text extraction service.

Pipeline:
  1. Try PyMuPDF direct text extraction.
  2. If result is empty / low-density → fallback to Tesseract OCR.
  3. Estimate confidence and return a structured result.

OCR fallback requires Tesseract to be installed on the system.
On Windows: https://github.com/UB-Mannheim/tesseract/wiki
On Linux:   sudo apt-get install tesseract-ocr
"""

from __future__ import annotations

import asyncio
import io
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


MAX_CONTEXT_CHARS = 14_000

MIN_CHARS_PER_PAGE = 40

MAX_OCR_PAGES = 25






@dataclass
class ExtractionResult:
    text: str
    method: str
    confidence: float
    page_count: int
    char_count: int
    warning: Optional[str] = None






def _pymupdf_confidence(text: str, page_count: int) -> float:
    if not text.strip():
        return 0.0
    density = len(text) / max(page_count, 1)
    if density > 300:
        return 0.95
    if density > 150:
        return 0.88
    if density > MIN_CHARS_PER_PAGE:
        return 0.72
    return 0.40






def _ocr_sync(pdf_bytes: bytes, page_count: int) -> ExtractionResult:
    """Render PDF pages → PIL images → Tesseract OCR."""
    try:
        import fitz
        import pytesseract
        from pytesseract import Output
        from PIL import Image
    except ImportError as exc:
        return ExtractionResult(
            text="",
            method="failed",
            confidence=0.0,
            page_count=page_count,
            char_count=0,
            warning=f"OCR dependencies missing: {exc}. Install pytesseract + Pillow.",
        )


    try:
        pytesseract.get_tesseract_version()
    except Exception:
        return ExtractionResult(
            text="",
            method="failed",
            confidence=0.0,
            page_count=page_count,
            char_count=0,
            warning=(
                "Tesseract OCR is not installed or not on PATH. "
                "Download from https://github.com/UB-Mannheim/tesseract/wiki"
            ),
        )

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_to_ocr = min(len(doc), MAX_OCR_PAGES)
    all_text: list[str] = []
    all_conf: list[float] = []

    for page_num in range(pages_to_ocr):
        page = doc[page_num]

        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))


        data = pytesseract.image_to_data(img, output_type=Output.DICT, lang="eng")
        words: list[str] = []
        for i, conf in enumerate(data["conf"]):
            try:
                conf_val = float(conf)
            except (ValueError, TypeError):
                continue
            if conf_val > 0:
                all_conf.append(conf_val)
                word = str(data["text"][i]).strip()
                if word:
                    words.append(word)
        all_text.append(" ".join(words))

    doc.close()
    text = "\n\n".join(all_text).strip()
    avg_conf = (sum(all_conf) / len(all_conf) / 100) if all_conf else 0.0

    warning = None
    if pages_to_ocr < page_count:
        warning = f"OCR limited to first {MAX_OCR_PAGES} of {page_count} pages."

    return ExtractionResult(
        text=text,
        method="ocr",
        confidence=round(avg_conf, 3),
        page_count=page_count,
        char_count=len(text),
        warning=warning,
    )






async def extract_pdf_text(pdf_bytes: bytes, filename: str = "document.pdf") -> ExtractionResult:
    """
    Full extraction pipeline. Tries PyMuPDF first; falls back to OCR.
    Always returns an ExtractionResult — never raises.
    """
    try:
        import fitz
    except ImportError:
        return ExtractionResult(
            text="",
            method="failed",
            confidence=0.0,
            page_count=0,
            char_count=0,
            warning="PyMuPDF not installed. Run: pip install PyMuPDF",
        )


    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        pages: list[str] = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()

        raw_text = "\n\n".join(pages).strip()
        confidence = _pymupdf_confidence(raw_text, page_count)

        if raw_text and confidence >= 0.50:
            log.info("PDF '%s': PyMuPDF extracted %d chars (conf %.2f)", filename, len(raw_text), confidence)
            return ExtractionResult(
                text=raw_text[:MAX_CONTEXT_CHARS],
                method="pymupdf",
                confidence=confidence,
                page_count=page_count,
                char_count=len(raw_text),
                warning="Text truncated to 14 000 characters." if len(raw_text) > MAX_CONTEXT_CHARS else None,
            )

        log.info("PDF '%s': PyMuPDF low confidence (%.2f) — attempting OCR.", filename, confidence)
    except Exception as exc:
        log.warning("PyMuPDF failed for '%s': %s", filename, exc)
        page_count = 0


    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = await loop.run_in_executor(pool, _ocr_sync, pdf_bytes, page_count)

    if result.text:
        result.text = result.text[:MAX_CONTEXT_CHARS]
        log.info("PDF '%s': OCR extracted %d chars (conf %.2f)", filename, result.char_count, result.confidence)

    return result
