"""PDF upload and extraction route."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.schemas import PDFExtractionResult, PDFUploadResponse
from app.services import pdf_context_store
from app.services.pdf_service import extract_pdf_text

router = APIRouter(prefix="/pdf", tags=["PDF"])

_MAX_PDF_SIZE_MB = 50


@router.post(
    "/upload",
    response_model=PDFUploadResponse,
    summary="Upload a PDF — extract text (PyMuPDF) with OCR fallback",
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to extract text from"),
) -> PDFUploadResponse:
    """
    Accepts a single PDF, extracts its text, and returns:
    - **extracted_text** — full text (truncated to 14 000 chars)
    - **method** — `pymupdf` (direct) or `ocr` (Tesseract) or `failed`
    - **confidence** — 0–1 float
    - **pdf_id** — pass this back in `/chat/stream` requests to ground the agent

    The extracted text is stored server-side; the chat endpoint retrieves it
    by `pdf_id` and injects it into the LLM context automatically.
    """

    ct = file.content_type or ""
    if ct not in ("application/pdf", "application/octet-stream") and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted.",
        )

    content = await file.read()


    max_bytes = _MAX_PDF_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds the {_MAX_PDF_SIZE_MB} MB limit.",
        )


    extraction = await extract_pdf_text(content, filename=file.filename or "document.pdf")

    if extraction.method == "failed" and not extraction.text:

        pass


    pdf_id = pdf_context_store.put(extraction)

    result = PDFExtractionResult(
        pdf_id=pdf_id,
        original_name=file.filename or "document.pdf",
        method=extraction.method,
        confidence=extraction.confidence,
        page_count=extraction.page_count,
        char_count=extraction.char_count,
        extracted_text=extraction.text,
        preview=extraction.text[:600],
        warning=extraction.warning,
    )

    return PDFUploadResponse(result=result)


@router.delete("/{pdf_id}", summary="Remove a stored PDF context")
async def delete_pdf(pdf_id: str):
    """Removes the server-side PDF context. Call when the user clears the PDF."""
    pdf_context_store.delete(pdf_id)
    return {"deleted": pdf_id}
