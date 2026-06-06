import { useState, useCallback } from 'react';
import { uploadAudio, deleteAudio } from '../api/client';
import type { AudioTranscriptionResult } from '../types';

export function useAudioUpload() {
  const [audioResult, setAudioResult] = useState<AudioTranscriptionResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stage, setStage] = useState<'idle' | 'uploading' | 'transcribing' | 'summarizing'>('idle');

  const upload = useCallback(async (file: File) => {
    if (!file) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(5);
    setStage('uploading');

    
    const timer = setInterval(() => {
      setUploadProgress((p) => {
        if (p < 30) { setStage('uploading'); return p + 3; }
        if (p < 70) { setStage('transcribing'); return p + 2; }
        if (p < 88) { setStage('summarizing'); return p + 1; }
        return p;
      });
    }, 500);

    try {
      const response = await uploadAudio(file);
      clearInterval(timer);
      setUploadProgress(100);
      setStage('idle');
      setAudioResult(response.result);
    } catch (err: unknown) {
      clearInterval(timer);
      const msg = err instanceof Error ? err.message : 'Audio upload failed.';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 600);
    }
  }, []);

  const clearAudio = useCallback(async () => {
    if (audioResult?.audio_id) {
      deleteAudio(audioResult.audio_id).catch(() => {});
    }
    setAudioResult(null);
    setUploadError(null);
    setStage('idle');
  }, [audioResult]);

  return {
    audioResult,
    isUploading,
    uploadError,
    uploadProgress,
    stage,
    upload,
    clearAudio,
    audioId: audioResult?.audio_id ?? null,
  };
}
