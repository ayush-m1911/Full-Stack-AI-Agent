"""File upload service."""

import os
import uuid
import aiofiles
from typing import List

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.models.schemas import UploadedFile


def _ensure_upload_dir() -> str:
    path = settings.UPLOAD_DIR
    os.makedirs(path, exist_ok=True)
    return path


async def save_uploads(files: List[UploadFile]) -> List[UploadedFile]:
    upload_dir = _ensure_upload_dir()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    results: List[UploadedFile] = []

    for file in files:
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type '{file.content_type}' is not allowed.",
            )


        content = await file.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{file.filename}' exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
            )


        ext = os.path.splitext(file.filename or "file")[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(upload_dir, stored_name)

        async with aiofiles.open(dest, "wb") as out:
            await out.write(content)

        results.append(
            UploadedFile(
                original_name=file.filename or stored_name,
                content_type=file.content_type or "application/octet-stream",
                size_bytes=len(content),
                stored_name=stored_name,
            )
        )

    return results
