"""File upload route."""

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from typing import List
from app.models.schemas import UploadResponse
from app.services.upload_service import save_uploads

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=UploadResponse, summary="Upload one or more files")
async def upload_files(
    files: List[UploadFile] = File(..., description="Files to upload (max 50 MB each)"),
) -> UploadResponse:
    """
    Accepts multiple files, validates their MIME type and size, stores them on
    disk, and returns metadata (ID, name, type, size) for each uploaded file.
    The returned file IDs can be passed back in chat requests.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided.",
        )

    uploaded = await save_uploads(files)
    return UploadResponse(files=uploaded, count=len(uploaded))
