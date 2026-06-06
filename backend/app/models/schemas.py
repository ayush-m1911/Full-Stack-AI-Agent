

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid




IntentType = Literal["summarize", "sentiment", "qa", "explain", "followup", "unknown"]



class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_ids: Optional[List[str]] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1, max_length=32_000)
    file_ids: Optional[List[str]] = None
    pdf_id: Optional[str] = None     
    image_id: Optional[str] = None    
    audio_id: Optional[str] = None   


class TraceStep(BaseModel):
    step: int
    name: str
    status: Literal["pending", "running", "done", "error"] = "pending"
    detail: Optional[str] = None
    duration_ms: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: str
    message: ChatMessage
    trace: List[TraceStep] = []
    result: Optional[str] = None
    extracted_text: Optional[str] = None
    detected_intent: Optional[IntentType] = None
    needs_followup: bool = False
    followup_question: Optional[str] = None



class StreamEvent(BaseModel):
    """Sent as JSON lines over SSE."""
    type: Literal[
        "trace",
        "intent",
        "token",
        "result",
        "error",
        "done",
        "followup",
        "pdf_context",
        "image_context",
        "audio_context",   
    ]
    data: Optional[str] = None
    trace_step: Optional[TraceStep] = None
    detected_intent: Optional[IntentType] = None



class PDFExtractionResult(BaseModel):
    pdf_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_name: str
    method: Literal["pymupdf", "ocr", "failed"]
    confidence: float = Field(ge=0.0, le=1.0)
    page_count: int = 0
    char_count: int = 0
    extracted_text: str = ""
    preview: str = ""
    warning: Optional[str] = None


class PDFUploadResponse(BaseModel):
    result: PDFExtractionResult



class ImageContentType(str):
    """Discriminator: 'code' | 'text' | 'mixed' | 'empty'."""


class ImageExtractionResult(BaseModel):
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_name: str
    content_type: Literal["code", "text", "mixed", "empty"] = "text"
    detected_language: Optional[str] = None
    ocr_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    char_count: int = 0
    extracted_text: str = ""
    preview: str = ""
    width: int = 0
    height: int = 0
    warning: Optional[str] = None


class ImageUploadResponse(BaseModel):
    result: ImageExtractionResult




class AudioSummaries(BaseModel):
    one_line: str = ""        
    bullets: List[str] = []  
    paragraph: str = ""     


class AudioTranscriptionResult(BaseModel):
    audio_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_name: str
    duration_seconds: float = 0.0
    whisper_model: str = "base"
    language: Optional[str] = None
    word_count: int = 0
    char_count: int = 0
    transcript: str = ""
    preview: str = ""         
    summaries: AudioSummaries = Field(default_factory=AudioSummaries)
    warning: Optional[str] = None


class AudioUploadResponse(BaseModel):
    result: AudioTranscriptionResult




class UploadedFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_name: str
    content_type: str
    size_bytes: int
    stored_name: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class UploadResponse(BaseModel):
    files: List[UploadedFile]
    count: int




class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    app_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)




class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Session"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0


class SessionListResponse(BaseModel):
    sessions: List[Session]




MultiIntentType = Literal[
    "summarize",
    "sentiment",
    "question_answering",
    "code_explanation",
    "comparison",
    "general_chat",
    "followup",
    "unknown",
]


class ExtractedSource(BaseModel):
    """Result from a single extraction module (PDF / Image / Audio / Text)."""
    source_type: Literal["pdf", "image", "audio", "text", "url"]
    filename: str = ""
    extracted_text: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    metadata: dict = Field(default_factory=dict)
    warning: Optional[str] = None
    status: Literal["success", "failed", "empty"] = "success"


class UnifiedContext(BaseModel):
    """All sources merged into a single LLM-ready context blob."""
    text_inputs: str = ""
    image_text: str = ""
    pdf_text: str = ""
    audio_transcript: str = ""
    pdf_content: str = ""
    image_content: str = ""
    audio_content: str = ""
    url_content: str = ""
    combined_context: str = ""   


class PlanStep(BaseModel):
    """One step in the agent's execution plan."""
    step: int
    tool: str
    status: Literal["pending", "running", "success", "failed"] = "pending"
    detail: Optional[str] = None
    duration_ms: Optional[int] = None


class MultiAnalysisResult(BaseModel):
    """Full result from the multi-input analysis pipeline."""
    extracted_sources: List[ExtractedSource] = []
    unified_context: UnifiedContext = Field(default_factory=UnifiedContext)
    detected_intent: MultiIntentType = "general_chat"
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    plan_trace: List[PlanStep] = []
    urls_detected: List[str] = []
    combined_context: str = ""
    result: str = ""


class MultiAnalysisResponse(BaseModel):
    """HTTP response wrapper."""
    data: MultiAnalysisResult
