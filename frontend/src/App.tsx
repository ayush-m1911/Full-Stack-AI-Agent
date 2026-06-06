import { useEffect, useRef } from 'react';
import { Trash2, AlertCircle } from 'lucide-react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { MessageHistory } from './components/Chat/MessageHistory';
import { InputBox } from './components/Chat/InputBox';
import { AgentTrace } from './components/AgentTrace/AgentTrace';
import { ResultPanel } from './components/ResultPanel/ResultPanel';
import { IntentBadge } from './components/Chat/IntentBadge';
import { ErrorBoundary } from './components/ErrorBoundary';


import { useChat } from './hooks/useChat';
import { useFileUpload } from './hooks/useFileUpload';
import { usePDFUpload } from './hooks/usePDFUpload';
import { useImageUpload } from './hooks/useImageUpload';
import { useAudioUpload } from './hooks/useAudioUpload';
import { useMultiAnalysis } from './hooks/useMultiAnalysis';


import type { TraceStep, TraceStatus } from './types';

export default function App() {
  
  const {
    messages,
    trace,
    result,
    detectedIntent,
    isLoading,
    error,
    send,
    clearSession,
    sessionId,
    addCustomMessage,
  } = useChat();

  
  const {
    uploadedFiles,
    clearFiles,
  } = useFileUpload();
  void uploadedFiles;

  const {
    clearPDF,
    pdfId,
  } = usePDFUpload();

  const {
    clearImage,
    imageId,
  } = useImageUpload();

  const {
    clearAudio,
    audioId,
  } = useAudioUpload();

  
  const multiAnalysis = useMultiAnalysis();
  const lastMultiResultRef = useRef<any>(null);

  
  useEffect(() => {
    if (multiAnalysis?.result && multiAnalysis.result !== lastMultiResultRef.current) {
      lastMultiResultRef.current = multiAnalysis.result;
      if (typeof addCustomMessage === 'function') {
        addCustomMessage('assistant', multiAnalysis.result.result || 'No response available.');
      }
    }
  }, [multiAnalysis?.result, addCustomMessage]);

  const allFiles = [
    ...(multiAnalysis?.pdfFiles || []),
    ...(multiAnalysis?.imageFiles || []),
    ...(multiAnalysis?.audioFiles || []),
  ];

  const handleSend = async (message: string) => {
    const hasFiles = allFiles.length > 0;
    const hasUrls = message.includes('http://') || message.includes('https://');
    if (hasFiles || hasUrls) {
      const filesCount = allFiles.length;
      if (typeof addCustomMessage === 'function') {
        addCustomMessage('user', message, filesCount > 0 ? filesCount : undefined);
      }
      if (multiAnalysis && typeof multiAnalysis.analyze === 'function') {
        await multiAnalysis.analyze(message);
      }
    } else {
      if (typeof send === 'function') {
        await send(message, []);
      }
    }
  };

  const handleRemoveFile = (idx: number) => {
    let current = idx;
    const pdfs = multiAnalysis?.pdfFiles || [];
    const images = multiAnalysis?.imageFiles || [];
    const audios = multiAnalysis?.audioFiles || [];

    if (current < pdfs.length) {
      if (multiAnalysis && typeof multiAnalysis.removePdf === 'function') {
        multiAnalysis.removePdf(current);
      }
      return;
    }
    current -= pdfs.length;
    if (current < images.length) {
      if (multiAnalysis && typeof multiAnalysis.removeImage === 'function') {
        multiAnalysis.removeImage(current);
      }
      return;
    }
    current -= images.length;
    if (current < audios.length) {
      if (multiAnalysis && typeof multiAnalysis.removeAudio === 'function') {
        multiAnalysis.removeAudio(current);
      }
      return;
    }
  };

  const handleClear = () => {
    if (typeof clearSession === 'function') clearSession();
    if (typeof clearFiles === 'function') clearFiles();
    if (typeof clearPDF === 'function') clearPDF();
    if (typeof clearImage === 'function') clearImage();
    if (typeof clearAudio === 'function') clearAudio();
    if (multiAnalysis && typeof multiAnalysis.clearAll === 'function') {
      multiAnalysis.clearAll();
    }
    lastMultiResultRef.current = null;
  };

  const activeTrace = (() => {
    if (multiAnalysis?.isLoading) {
      const stage = multiAnalysis?.stage || 'idle';
      const steps: TraceStep[] = [];
      const stageList: { stage: typeof stage; label: string }[] = [
        { stage: 'uploading', label: 'Uploading files' },
        { stage: 'extracting', label: 'Extracting content' },
        { stage: 'building_context', label: 'Building context' },
        { stage: 'detecting_intent', label: 'Detecting intent' },
        { stage: 'generating', label: 'Generating response' },
      ];

      let foundActive = false;
      stageList.forEach((item, index) => {
        if (foundActive) {
          steps.push({ step: index + 1, name: item.label, status: 'pending' });
        } else if (item.stage === stage) {
          steps.push({ step: index + 1, name: item.label, status: 'running' });
          foundActive = true;
        } else {
          steps.push({ step: index + 1, name: item.label, status: 'done' });
        }
      });
      return steps;
    }

    if (multiAnalysis?.result?.plan_trace && Array.isArray(multiAnalysis.result.plan_trace)) {
      return multiAnalysis.result.plan_trace.map((step, idx): TraceStep => ({
        step: step?.step ?? idx + 1,
        name: step?.tool || 'Step',
        status: (step?.status === 'success' ? 'done' : step?.status === 'failed' ? 'error' : step?.status || 'pending') as TraceStatus,
        detail: step?.detail || undefined,
        duration_ms: step?.duration_ms || undefined,
      }));
    }

    return Array.isArray(trace) ? trace : [];
  })();

  const activeResult = multiAnalysis?.result ? multiAnalysis.result.result : result;
  const activeIntent = multiAnalysis?.result ? (multiAnalysis.result.detected_intent as any) : detectedIntent;
  const activeLoading = isLoading || multiAnalysis?.isLoading;
  const activeError = error || multiAnalysis?.error;

  return (
    <div className="flex flex-col md:flex-row h-screen w-screen overflow-hidden" style={{ background: 'var(--color-bg-base)' }}>
      <Sidebar />

      <div className="flex flex-col md:flex-row flex-1 overflow-y-auto md:overflow-hidden gap-3 p-3">
        { }
        <ErrorBoundary title="Chat Workspace">
          <div
            className="flex flex-col flex-1 min-w-0 rounded-2xl overflow-hidden h-[600px] md:h-full"
            style={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)' }}
          >
            { }
            <div
              className="flex items-center justify-between px-5 py-3.5"
              style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
            >
              <div className="flex items-center gap-3">
                <div>
                  <h1 className="text-sm font-bold gradient-text">AI Agent Chat</h1>
                  <p className="text-xs mt-0.5 flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                    Session: {sessionId ? sessionId.slice(0, 8) : 'new'}&hellip;
                    {pdfId && (
                      <span
                        className="inline-flex items-center gap-1 rounded-full text-[9px] px-1.5 py-0.5 font-semibold"
                        style={{ background: 'rgba(239,68,68,0.12)', color: '#f87171' }}
                      >
                        PDF active
                      </span>
                    )}
                    {imageId && (
                      <span
                        className="inline-flex items-center gap-1 rounded-full text-[9px] px-1.5 py-0.5 font-semibold"
                        style={{ background: 'rgba(139,92,246,0.12)', color: '#a78bfa' }}
                      >
                        Image active
                      </span>
                    )}
                    {audioId && (
                      <span
                        className="inline-flex items-center gap-1 rounded-full text-[9px] px-1.5 py-0.5 font-semibold"
                        style={{ background: 'rgba(245,158,11,0.12)', color: '#fbbf24' }}
                      >
                        Audio active
                      </span>
                    )}
                  </p>
                </div>
                {activeIntent && activeIntent !== 'unknown' && (
                  <IntentBadge intent={activeIntent} size="md" />
                )}
              </div>
              <button
                onClick={handleClear}
                className="btn-ghost"
                style={{ padding: '6px 12px' }}
                title="Clear session"
              >
                <Trash2 size={13} />
                <span>Clear</span>
              </button>
            </div>

            { }
            <MessageHistory messages={messages} />

            { }
            {activeError && (
              <div
                className="mx-4 mb-2 flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm animate-fade-up"
                style={{ background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.25)', color: '#fda4af' }}
              >
                <AlertCircle size={14} />
                {activeError}
              </div>
            )}

            { }
            <div className="p-3">
              <InputBox
                onSend={handleSend}
                isLoading={activeLoading}
                files={allFiles}
                onAttachFiles={multiAnalysis?.addFiles}
                onRemoveFile={handleRemoveFile}
                onClearFiles={multiAnalysis?.clearAll}
              />
            </div>
          </div>
        </ErrorBoundary>

        { }
        <div className="flex flex-col w-full md:w-80 flex-shrink-0 gap-3">
          { }
          <ErrorBoundary title="Agent Trace Panel">
            <div className="flex-1" style={{ minHeight: '180px' }}>
              <AgentTrace trace={activeTrace} detectedIntent={activeIntent} />
            </div>
          </ErrorBoundary>

          { }
          <ErrorBoundary title="Final Response Panel">
            <div className="flex-1" style={{ minHeight: '160px' }}>
              <ResultPanel result={activeResult} />
            </div>
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}
