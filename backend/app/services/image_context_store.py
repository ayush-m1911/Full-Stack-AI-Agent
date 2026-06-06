"""In-memory image context store (image_id → ImageExtractionData)."""

from __future__ import annotations
import uuid
from typing import Optional
from app.services.image_service import ImageExtractionData

_store: dict[str, ImageExtractionData] = {}


def put(data: ImageExtractionData) -> str:
    """Store image data and return a fresh image_id."""
    image_id = str(uuid.uuid4())
    _store[image_id] = data
    return image_id


def get(image_id: str) -> Optional[ImageExtractionData]:
    return _store.get(image_id)


def delete(image_id: str) -> None:
    _store.pop(image_id, None)
