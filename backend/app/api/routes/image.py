"""Image upload and OCR extraction route."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.models.schemas import ImageExtractionResult, ImageUploadResponse
from app.services import image_context_store
from app.services.image_service import extract_image_text

router = APIRouter(prefix="/image", tags=["Image"])

ACCEPTED_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp"}
MAX_IMAGE_MB = 20


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    summary="Upload PNG/JPG — OCR text extraction + code detection",
)
async def upload_image(
    file: UploadFile = File(..., description="PNG or JPG image to analyse"),
) -> ImageUploadResponse:
    """
    Accepts a single image, runs EasyOCR, detects code vs text, and returns:
    - **extracted_text** — full OCR text (up to 12 000 chars)
    - **ocr_confidence** — 0–1 average word confidence
    - **content_type** — `code` | `text` | `mixed` | `empty`
    - **detected_language** — programming language if code detected
    - **image_id** — pass back in `/chat/stream` to ground the agent

    The image context is stored server-side for retrieval by the chat endpoint.
    """
    ct = file.content_type or ""
    name = (file.filename or "image").lower()
    if ct not in ACCEPTED_MIME and not any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PNG, JPG, WEBP, or BMP images are accepted.",
        )

    content = await file.read()

    if len(content) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {MAX_IMAGE_MB} MB limit.",
        )

    data = await extract_image_text(content, filename=file.filename or "image")
    image_id = image_context_store.put(data)

    result = ImageExtractionResult(
        image_id=image_id,
        original_name=file.filename or "image",
        content_type=data.content_type,
        detected_language=data.detected_language,
        ocr_confidence=data.ocr_confidence,
        char_count=len(data.text),
        extracted_text=data.text,
        preview=data.text[:500],
        width=data.width,
        height=data.height,
        warning=data.warning,
    )
    return ImageUploadResponse(result=result)


@router.delete("/{image_id}", summary="Remove stored image context")
async def delete_image(image_id: str):
    image_context_store.delete(image_id)
    return {"deleted": image_id}
