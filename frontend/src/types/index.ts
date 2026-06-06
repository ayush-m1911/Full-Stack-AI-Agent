

export type MessageRole = 'user' | 'assistant' | 'system';
export type TraceStatus = 'pending' | 'running' | 'done' | 'error';

export type IntentType =
  | 'summarize'
  | 'sentiment'
  | 'qa'
  | 'explain'
  | 'followup'
  | 'unknown';

export type StreamEventType =
  | 'trace'
  | 'intent'
  | 'token'
  | 'result'
  | 'error'
  | 'done'
  | 'followup'
  | 'pdf_context'
  | 'image_context'
  | 'audio_context';

export type PDFMethod = 'pymupdf' | 'ocr' | 'failed';
export type ImageContentType = 'code' | 'text' | 'mixed' | 'empty';

export interface TraceStep {
  step: number;
  name: string;
  status: TraceStatus;
  detail?: string;
  duration_ms?: number;
}

export interface StreamEvent {
  type: StreamEventType;
  data?: string;
  trace_step?: TraceStep;
  detected_intent?: IntentType;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  file_ids?: string[];
}

export interface ChatSession {
  id: string;
  name: string;
  created_at: string;
  message_count: number;
}

export interface UploadedFile {
  id: string;
  original_name: string;
  content_type: string;
  size_bytes: number;
  stored_name: string;
  uploaded_at: string;
}

export interface ChatRequest {
  session_id?: string;
  message: string;
  file_ids?: string[];
  pdf_id?: string;
  image_id?: string;
  audio_id?: string;
}

export interface ChatResponse {
  session_id: string;
  message: ChatMessage;
  trace: TraceStep[];
  result?: string;
  extracted_text?: string;
  detected_intent?: IntentType;
  needs_followup?: boolean;
  followup_question?: string;
}

export interface UploadResponse {
  files: UploadedFile[];
  count: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
  timestamp: string;
}



export interface PDFExtractionResult {
  pdf_id: string;
  original_name: string;
  method: PDFMethod;
  confidence: number;
  page_count: number;
  char_count: number;
  extracted_text: string;
  preview: string;
  warning?: string | null;
}

export interface PDFUploadResponse {
  result: PDFExtractionResult;
}



export interface ImageExtractionResult {
  image_id: string;
  original_name: string;
  content_type: ImageContentType;
  detected_language: string | null;
  ocr_confidence: number;       
  char_count: number;
  extracted_text: string;
  preview: string;              
  width: number;
  height: number;
  warning?: string | null;
}

export interface ImageUploadResponse {
  result: ImageExtractionResult;
}



export interface AudioSummaries {
  one_line: string;
  bullets: string[];
  paragraph: string;
}

export interface AudioTranscriptionResult {
  audio_id: string;
  original_name: string;
  duration_seconds: number;   
  whisper_model: string;
  language: string | null;
  word_count: number;
  char_count: number;
  transcript: string;
  preview: string;            
  summaries: AudioSummaries;
  warning?: string | null;
}

export interface AudioUploadResponse {
  result: AudioTranscriptionResult;
}



export interface LocalMessage extends ChatMessage {
  isStreaming?: boolean;
  streamedContent?: string;
  detectedIntent?: IntentType;
  isFollowup?: boolean;
}

export interface AppState {
  sessionId: string | null;
  messages: LocalMessage[];
  trace: TraceStep[];
  result: string | null;
  detectedIntent: IntentType | null;
  isLoading: boolean;
  uploadedFiles: UploadedFile[];
}



export type MultiIntentType =
  | 'summarize'
  | 'sentiment'
  | 'question_answering'
  | 'code_explanation'
  | 'comparison'
  | 'general_chat'
  | 'followup'
  | 'unknown';

export type SourceType = 'pdf' | 'image' | 'audio' | 'text' | 'url';
export type SourceStatus = 'success' | 'failed' | 'empty';

export interface ExtractedSource {
  source_type: SourceType;
  filename: string;
  extracted_text: string;
  confidence: number;         
  metadata: Record<string, unknown>;
  warning?: string | null;
  status: SourceStatus;
}

export interface UnifiedContext {
  text_inputs: string;
  image_text: string;
  pdf_text: string;
  audio_transcript: string;
  pdf_content: string;
  image_content: string;
  audio_content: string;
  url_content: string;
  combined_context: string;
}

export interface PlanStep {
  step: number;
  tool: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  detail?: string | null;
  duration_ms?: number | null;
}

export interface MultiAnalysisResult {
  extracted_sources: ExtractedSource[];
  unified_context: UnifiedContext;
  detected_intent: MultiIntentType;
  requires_clarification: boolean;
  clarification_question?: string | null;
  plan_trace: PlanStep[];
  urls_detected: string[];
  combined_context: string;
  result: string;
}

export interface MultiAnalysisResponse {
  data: MultiAnalysisResult;
}
