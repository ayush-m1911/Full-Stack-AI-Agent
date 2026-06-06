import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  StreamEvent,
  UploadResponse,
  HealthResponse,
  PDFUploadResponse,
  ImageUploadResponse,
  AudioUploadResponse,
  MultiAnalysisResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
});



export const sendMessage = async (payload: ChatRequest): Promise<ChatResponse> => {
  const { data } = await apiClient.post<ChatResponse>('/chat', payload);
  return data;
};

export const fetchSessions = async () => {
  const { data } = await apiClient.get('/chat/sessions');
  return data;
};

export const fetchSessionHistory = async (sessionId: string) => {
  const { data } = await apiClient.get(`/chat/sessions/${sessionId}/history`);
  return data;
};



export async function streamMessage(
  payload: ChatRequest,
  onEvent: (event: StreamEvent) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): Promise<void> {
  const url = `${BASE_URL}/api/v1/chat/stream`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    onError(err instanceof Error ? err : new Error('Network error'));
    return;
  }

  if (!response.ok || !response.body) {
    onError(new Error(`Server error: ${response.status} ${response.statusText}`));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        const stripped = line.startsWith('data: ') ? line.slice(6).trim() : line.trim();
        if (!stripped) continue;
        try {
          const event: StreamEvent = JSON.parse(stripped);
          onEvent(event);
          if (event.type === 'done') { onDone(); return; }
        } catch {   }
      }
    }
    onDone();
  } catch (err) {
    onError(err instanceof Error ? err : new Error('Stream read error'));
  } finally {
    reader.releaseLock();
  }
}



export async function uploadPDF(file: File): Promise<PDFUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<PDFUploadResponse>('/pdf/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120_000,
  });
  return data;
}

export async function deletePDF(pdfId: string): Promise<void> {
  await apiClient.delete(`/pdf/${pdfId}`);
}



export async function uploadImage(file: File): Promise<ImageUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<ImageUploadResponse>('/image/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120_000,  
  });
  return data;
}

export async function deleteImage(imageId: string): Promise<void> {
  await apiClient.delete(`/image/${imageId}`);
}



export async function uploadAudio(file: File): Promise<AudioUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<AudioUploadResponse>('/audio/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300_000,  
  });
  return data;
}

export async function deleteAudio(audioId: string): Promise<void> {
  await apiClient.delete(`/audio/${audioId}`);
}




export const uploadFiles = async (files: File[]): Promise<UploadResponse> => {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));
  const { data } = await apiClient.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};



export const fetchHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
};



export async function analyzeMultiInput(
  query: string,
  files: File[],
): Promise<MultiAnalysisResponse> {
  const formData = new FormData();
  formData.append('query', query);
  files.forEach((f) => formData.append('files', f));
  const { data } = await apiClient.post<MultiAnalysisResponse>('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600_000, 
  });
  return data;
}
