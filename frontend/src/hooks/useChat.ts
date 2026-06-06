import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { streamMessage } from '../api/client';
import type { LocalMessage, TraceStep, UploadedFile, IntentType, StreamEvent } from '../types';

export function useChat() {
  const [sessionId, setSessionId] = useState<string>(() => uuidv4());
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [detectedIntent, setDetectedIntent] = useState<IntentType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (
      content: string,
      uploadedFiles: UploadedFile[],
      pdfId?: string | null,
      imageId?: string | null,
      audioId?: string | null,
    ) => {
      if (!content.trim() || isLoading) return;

      setError(null);
      setTrace([]);
      setResult(null);
      setDetectedIntent(null);

      const userMsg: LocalMessage = {
        id: uuidv4(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
        file_ids: uploadedFiles.map((f) => f.id),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      const placeholderId = uuidv4();
      setMessages((prev) => [
        ...prev,
        {
          id: placeholderId,
          role: 'assistant',
          content: '',
          streamedContent: '',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ]);

      let accumulated = '';

      const handleEvent = (event: StreamEvent) => {
        switch (event.type) {
          case 'trace': {
            if (event.trace_step) {
              setTrace((prev) => {
                const idx = prev.findIndex((s) => s.step === event.trace_step!.step);
                if (idx >= 0) {
                  const next = [...prev];
                  next[idx] = event.trace_step!;
                  return next;
                }
                return [...prev, event.trace_step!];
              });
            }
            break;
          }
          case 'intent': {
            const intent = event.detected_intent ?? null;
            setDetectedIntent(intent);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === placeholderId ? { ...m, detectedIntent: intent ?? undefined } : m,
              ),
            );
            break;
          }
          case 'token': {
            accumulated += event.data ?? '';
            setMessages((prev) =>
              prev.map((m) =>
                m.id === placeholderId ? { ...m, streamedContent: accumulated } : m,
              ),
            );
            break;
          }
          case 'followup': {
            const text = event.data ?? '';
            accumulated = text;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === placeholderId
                  ? { ...m, streamedContent: text, isFollowup: true }
                  : m,
              ),
            );
            break;
          }
          case 'result': {
            setResult(event.data ?? null);
            break;
          }
          case 'pdf_context':
          case 'image_context':
          case 'audio_context': {
            
            break;
          }
          case 'error': {
            setError(event.data ?? 'Unknown error from agent');
            break;
          }
          default:
            break;
        }
      };

      const handleDone = () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId
              ? { ...m, content: accumulated, streamedContent: undefined, isStreaming: false }
              : m,
          ),
        );
        setIsLoading(false);
      };

      const handleError = (err: Error) => {
        setError(err.message);
        setMessages((prev) => prev.filter((m) => m.id !== placeholderId));
        setIsLoading(false);
      };

      await streamMessage(
        {
          session_id: sessionId,
          message: content,
          file_ids: uploadedFiles.map((f) => f.id),
          ...(pdfId ? { pdf_id: pdfId } : {}),
          ...(imageId ? { image_id: imageId } : {}),
          ...(audioId ? { audio_id: audioId } : {}),
        },
        handleEvent,
        handleDone,
        handleError,
      );
    },
    [sessionId, isLoading],
  );

  const addCustomMessage = useCallback((role: 'user' | 'assistant', content: string, filesCount?: number) => {
    const contentPrefix = role === 'user' && filesCount && filesCount > 0 
      ? `📎 [Multi-Input: ${filesCount} file${filesCount > 1 ? 's' : ''}]\n${content}`
      : content;
    setMessages((prev) => [
      ...prev,
      {
        id: uuidv4(),
        role,
        content: contentPrefix,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const clearSession = useCallback(() => {
    setSessionId(uuidv4());
    setMessages([]);
    setTrace([]);
    setResult(null);
    setDetectedIntent(null);
    setError(null);
  }, []);

  return { messages, trace, result, detectedIntent, isLoading, error, send, clearSession, sessionId, addCustomMessage };
}
