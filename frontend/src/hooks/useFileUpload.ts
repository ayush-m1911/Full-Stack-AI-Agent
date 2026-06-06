import { useState, useCallback } from 'react';
import { uploadFiles } from '../api/client';
import type { UploadedFile } from '../types';

export function useFileUpload() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const upload = useCallback(async (files: File[]) => {
    if (!files.length) return;
    setIsUploading(true);
    setUploadError(null);
    try {
      const response = await uploadFiles(files);
      setUploadedFiles((prev) => [...prev, ...response.files]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  }, []);

  const removeFile = useCallback((id: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const clearFiles = useCallback(() => setUploadedFiles([]), []);

  return { uploadedFiles, isUploading, uploadError, upload, removeFile, clearFiles };
}
