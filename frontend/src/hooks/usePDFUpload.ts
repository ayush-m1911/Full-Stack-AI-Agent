import { useState, useCallback } from 'react';
import { uploadPDF, deletePDF } from '../api/client';
import type { PDFExtractionResult } from '../types';

export function usePDFUpload() {
  const [pdfResult, setPdfResult] = useState<PDFExtractionResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const upload = useCallback(async (file: File) => {
    if (!file) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(10);

    try {
      
      const progressTimer = setInterval(() => {
        setUploadProgress((p) => Math.min(p + 5, 85));
      }, 500);

      const response = await uploadPDF(file);
      clearInterval(progressTimer);
      setUploadProgress(100);
      setPdfResult(response.result);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'PDF upload failed. Please try again.';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 600);
    }
  }, []);

  const clearPDF = useCallback(async () => {
    if (pdfResult?.pdf_id) {
      
      deletePDF(pdfResult.pdf_id).catch(() => {});
    }
    setPdfResult(null);
    setUploadError(null);
  }, [pdfResult]);

  return {
    pdfResult,
    isUploading,
    uploadError,
    uploadProgress,
    upload,
    clearPDF,
    pdfId: pdfResult?.pdf_id ?? null,
  };
}
