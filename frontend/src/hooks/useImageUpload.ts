import { useState, useCallback } from 'react';
import { uploadImage, deleteImage } from '../api/client';
import type { ImageExtractionResult } from '../types';

export function useImageUpload() {
  const [imageResult, setImageResult] = useState<ImageExtractionResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const upload = useCallback(async (file: File) => {
    if (!file) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(10);

    
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    try {
      const timer = setInterval(() => {
        setUploadProgress((p) => Math.min(p + 6, 85));
      }, 400);

      const response = await uploadImage(file);
      clearInterval(timer);
      setUploadProgress(100);
      setImageResult(response.result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Image upload failed.';
      setUploadError(msg);
      
      URL.revokeObjectURL(url);
      setPreviewUrl(null);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 600);
    }
  }, []);

  const clearImage = useCallback(async () => {
    if (imageResult?.image_id) {
      deleteImage(imageResult.image_id).catch(() => {});
    }
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setImageResult(null);
    setPreviewUrl(null);
    setUploadError(null);
  }, [imageResult, previewUrl]);

  return {
    imageResult,
    previewUrl,
    isUploading,
    uploadError,
    uploadProgress,
    upload,
    clearImage,
    imageId: imageResult?.image_id ?? null,
  };
}
