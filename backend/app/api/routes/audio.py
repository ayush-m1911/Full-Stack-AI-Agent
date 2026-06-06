"""Audio upload, transcription, and summary route."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.models.schemas import AudioUploadResponse, AudioTranscriptionResult, AudioSummaries
from app.services import audio_context_store
from app.services.audio_service import transcribe_audio

router = APIRouter(prefix="/audio", tags=["Audio"])

ACCEPTED_MIME = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/wave", "audio/mp4", "audio/m4a", "audio/x-m4a",
    "audio/ogg", "audio/flac", "audio/x-flac",
}
ACCEPTED_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".flac")
MAX_AUDIO_MB = 100


@router.post(
    "/upload",
    response_model=AudioUploadResponse,
    summary="Upload MP3/WAV/M4A — Whisper transcription + 3-format summaries",
)
async def upload_audio(
    file: UploadFile = File(..., description="MP3, WAV, or M4A audio file"),
) -> AudioUploadResponse:
    """
    Accepts an audio file, transcribes it with OpenAI Whisper, and returns:
    - **transcript** — full text (up to 14 000 chars)
    - **duration_seconds** — audio duration
    - **language** — detected language code (e.g. 'en')
    - **summaries.one_line** — single sentence summary
    - **summaries.bullets** — 3 bullet points
    - **summaries.paragraph** — 5-sentence paragraph
    - **audio_id** — pass back in `/chat/stream` for follow-up Q&A

    Requires FFmpeg on PATH for non-WAV formats.
    """
    ct = (file.content_type or "").lower()
    name = (file.filename or "audio").lower()

    if ct not in ACCEPTED_MIME and not any(name.endswith(ext) for ext in ACCEPTED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only MP3, WAV, M4A, OGG, or FLAC audio files are accepted.",
        )

    content = await file.read()

    if len(content) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds the {MAX_AUDIO_MB} MB limit.",
        )

    data = await transcribe_audio(content, filename=file.filename or "audio")
    audio_id = audio_context_store.put(data)

    def _fmt_duration(secs: float) -> str:
        m, s = divmod(int(secs), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    result = AudioTranscriptionResult(
        audio_id=audio_id,
        original_name=file.filename or "audio",
        duration_seconds=data.duration_seconds,
        whisper_model="base",
        language=data.language,
        word_count=data.word_count,
        char_count=data.char_count,
        transcript=data.transcript,
        preview=data.transcript[:400],
        summaries=AudioSummaries(
            one_line=data.summaries.get("one_line", ""),
            bullets=data.summaries.get("bullets", []),
            paragraph=data.summaries.get("paragraph", ""),
        ),
        warning=data.warning,
    )

    return AudioUploadResponse(result=result)


@router.delete("/{audio_id}", summary="Remove stored audio context")
async def delete_audio(audio_id: str):
    audio_context_store.delete(audio_id)
    return {"deleted": audio_id}
