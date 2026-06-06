"""
In-memory PDF context store.

Maps pdf_id → ExtractionResult so the agent can fetch
the extracted text during a chat stream.
"""

from __future__ import annotations
import uuid
from typing import Optional
from app.services.pdf_service import ExtractionResult

_store: dict[str, ExtractionResult] = {}


def put(result: ExtractionResult) -> str:
    """Store a result and return a new pdf_id."""
    pdf_id = str(uuid.uuid4())
    _store[pdf_id] = result
    return pdf_id


def get(pdf_id: str) -> Optional[ExtractionResult]:
    """Retrieve a result by pdf_id. Returns None if not found."""
    return _store.get(pdf_id)


def delete(pdf_id: str) -> None:
    _store.pop(pdf_id, None)


def size() -> int:
    return len(_store)
