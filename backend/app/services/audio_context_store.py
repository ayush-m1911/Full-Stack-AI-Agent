"""In-memory audio context store (audio_id → AudioTranscriptionData)."""

from __future__ import annotations
import uuid
from typing import Optional
from app.services.audio_service import AudioTranscriptionData

_store: dict[str, AudioTranscriptionData] = {}


def put(data: AudioTranscriptionData) -> str:
    """Store transcription data and return a fresh audio_id."""
    audio_id = str(uuid.uuid4())
    _store[audio_id] = data
    return audio_id


def get(audio_id: str) -> Optional[AudioTranscriptionData]:
    return _store.get(audio_id)


def delete(audio_id: str) -> None:
    _store.pop(audio_id, None)
