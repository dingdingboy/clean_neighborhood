import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Image as ImageIcon, Video, Mic, FileText } from 'lucide-react';
import { UploadedFile } from '@/types';

interface MediaDropzoneProps {
  onFilesSelected: (files: UploadedFile[]) => void;
  acceptedFiles?: string[];
  maxFiles?: number;
  maxSize?: number;
}

const FILE_TYPE_CONFIG = {
  'image': {
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp'] },
    icon: ImageIcon,
    label: 'Images',
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
  },
  'video': {
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.webm'] },
    icon: Video,
    label: 'Videos',
    color: 'text-purple-500',
    bgColor: 'bg-purple-50',
  },
  'audio': {
    accept: { 'audio/*': ['.mp3', '.wav', '.ogg', '.webm'] },
    icon: Mic,
    label: 'Audio',
    color: 'text-green-500',
    bgColor: 'bg-green-50',
  },
};

export function MediaDropzone({
  onFilesSelected,
  maxFiles = 10,
  maxSize = 100 * 1024 * 1024, // 100MB
}: MediaDropzoneProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const detectFileType = (file: File): 'image' | 'video' | 'audio' | null => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    return null;
  };

  const createPreview = (file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setError(null);

      if (files.length + acceptedFiles.length > maxFiles) {
        setError(`Maximum ${maxFiles} files allowed`);
        return;
      }

      const newFiles: UploadedFile[] = [];

      for (const file of acceptedFiles) {
        const type = detectFileType(file);
        if (!type) {
          setError(`Unsupported file type: ${file.name}`);
          continue;
        }

        const preview = await createPreview(file);
        newFiles.push({
          file,
          type,
          preview,
          progress: 0,
          uploaded: false,
        });
      }

      const updatedFiles = [...files, ...newFiles];
      setFiles(updatedFiles);
      onFilesSelected(updatedFiles);
    },
    [files, maxFiles, onFilesSelected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp'],
      'video/*': ['.mp4', '.avi', '.mov', '.webm'],
      'audio/*': ['.mp3', '.wav', '.ogg', '.webm'],
    },
  });

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    setFiles(updated);
    onFilesSelected(updated);
  };

  const updateProgress = (index: number, progress: number) => {
    setFiles((prev) =>
      prev.map((f, i) => (i === index ? { ...f, progress, uploaded: progress === 100 } : f))
    );
  };

  const getFileIcon = (type: string) => {
    const config = FILE_TYPE_CONFIG[type as keyof typeof FILE_TYPE_CONFIG];
    if (config) {
      const Icon = config.icon;
      return <Icon className={`w-8 h-8 ${config.color}`} />;
    }
    return <FileText className="w-8 h-8 text-gray-400" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700">
          {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          or click to select files
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Supports images, videos, and audio (max {formatFileSize(maxSize)})
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">
            Selected Files ({files.length})
          </h3>
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center p-3 bg-white border rounded-lg shadow-sm"
            >
              {/* Preview or icon */}
              <div className="flex-shrink-0 w-16 h-16 flex items-center justify-center bg-gray-50 rounded-md overflow-hidden">
                {file.preview ? (
                  <img
                    src={file.preview}
                    alt={file.file.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  getFileIcon(file.type)
                )}
              </div>

              {/* File info */}
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.file.size)} • {file.type}
                </p>

                {/* Progress bar */}
                {file.progress > 0 && (
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {file.uploaded ? 'Uploaded' : `${file.progress}%`}
                    </p>
                  </div>
                )}
              </div>

              {/* Remove button */}
              <button
                onClick={() => removeFile(index)}
                className="ml-4 p-1 text-gray-400 hover:text-red-500 transition-colors"
                disabled={file.uploaded}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default MediaDropzone;
