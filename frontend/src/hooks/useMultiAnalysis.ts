import { useState, useCallback, useRef } from 'react';
import { analyzeMultiInput } from '../api/client';
import type { MultiAnalysisResult } from '../types';

export type AnalysisStage =
  | 'idle'
  | 'uploading'
  | 'extracting'
  | 'building_context'
  | 'detecting_intent'
  | 'generating'
  | 'done'
  | 'error';

export function useMultiAnalysis() {
  const [result, setResult] = useState<MultiAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<AnalysisStage>('idle');
  const [progress, setProgress] = useState(0);

  
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [audioFiles, setAudioFiles] = useState<File[]>([]);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const allFiles = [...pdfFiles, ...imageFiles, ...audioFiles];
  const hasFiles = allFiles.length > 0;

  const addFiles = useCallback((incoming: File[]) => {
    for (const f of incoming) {
      const name = f.name.toLowerCase();
      if (name.endsWith('.pdf') || f.type === 'application/pdf') {
        setPdfFiles((p) => [...p, f]);
      } else if (f.type.startsWith('image/') || name.match(/\.(png|jpg|jpeg|webp)$/)) {
        setImageFiles((p) => [...p, f]);
      } else if (f.type.startsWith('audio/') || name.match(/\.(mp3|wav|m4a|ogg|flac)$/)) {
        setAudioFiles((p) => [...p, f]);
      }
    }
  }, []);

  const removePdf = useCallback((idx: number) =>
    setPdfFiles((p) => p.filter((_, i) => i !== idx)), []);
  const removeImage = useCallback((idx: number) =>
    setImageFiles((p) => p.filter((_, i) => i !== idx)), []);
  const removeAudio = useCallback((idx: number) =>
    setAudioFiles((p) => p.filter((_, i) => i !== idx)), []);

  const clearAll = useCallback(() => {
    setPdfFiles([]);
    setImageFiles([]);
    setAudioFiles([]);
    setResult(null);
    setError(null);
    setStage('idle');
    setProgress(0);
  }, []);

  
  const _startProgress = (hasAudio: boolean) => {
    setProgress(5);
    const stages: { stage: AnalysisStage; target: number; delay: number }[] = [
      { stage: 'uploading', target: 15, delay: 600 },
      { stage: 'extracting', target: hasAudio ? 45 : 35, delay: hasAudio ? 3000 : 800 },
      { stage: 'building_context', target: 60, delay: 600 },
      { stage: 'detecting_intent', target: 70, delay: 500 },
      { stage: 'generating', target: 90, delay: 1200 },
    ];

    let i = 0;
    const tick = () => {
      if (i >= stages.length) return;
      const s = stages[i++];
      setStage(s.stage);
      setProgress(s.target);
      timerRef.current = setTimeout(tick, s.delay);
    };
    timerRef.current = setTimeout(tick, 200);
  };

  const _stopProgress = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
  };

  const analyze = useCallback(
    async (query: string) => {
      if (!query.trim() || isLoading) return;
      if (allFiles.length === 0 && !query.trim()) return;

      setIsLoading(true);
      setError(null);
      setResult(null);
      setStage('uploading');
      setProgress(5);
      _startProgress(audioFiles.length > 0);

      try {
        const response = await analyzeMultiInput(query, [...pdfFiles, ...imageFiles, ...audioFiles]);
        _stopProgress();
        setProgress(100);
        setStage('done');
        setResult(response.data);
      } catch (err: unknown) {
        _stopProgress();
        const msg = err instanceof Error ? err.message : 'Analysis failed.';
        setError(msg);
        setStage('error');
      } finally {
        setIsLoading(false);
        setTimeout(() => setProgress(0), 800);
      }
    },
    
    [isLoading, pdfFiles, imageFiles, audioFiles],
  );

  return {
    result,
    isLoading,
    error,
    stage,
    progress,
    pdfFiles,
    imageFiles,
    audioFiles,
    hasFiles,
    allFiles,
    addFiles,
    removePdf,
    removeImage,
    removeAudio,
    clearAll,
    analyze,
  };
}
