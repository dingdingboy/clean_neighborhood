import React, { useEffect, useState } from 'react';
import { useReport } from '@/hooks';
import { useWebSocket } from '@/hooks';
import { ReportStatus as ReportStatusType, GeolocationData, AnalysisResult } from '@/types';
import { Clock, CheckCircle, XCircle, AlertCircle, MapPin, Shield, FileText, Phone, Globe } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ReportStatusProps {
  reportId: number;
  onClose?: () => void;
}

const STATUS_CONFIG: Record<ReportStatusType, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: 'Pending', color: 'text-gray-500', icon: <Clock className="w-5 h-5" /> },
  uploading: { label: 'Uploading', color: 'text-blue-500', icon: <Clock className="w-5 h-5" /> },
  analyzing: { label: 'Analyzing', color: 'text-yellow-500', icon: <Clock className="w-5 h-5" /> },
  review_required: { label: 'Review Required', color: 'text-orange-500', icon: <AlertCircle className="w-5 h-5" /> },
  approved: { label: 'Approved', color: 'text-green-500', icon: <CheckCircle className="w-5 h-5" /> },
  rejected: { label: 'Rejected', color: 'text-red-500', icon: <XCircle className="w-5 h-5" /> },
  submitting: { label: 'Submitting', color: 'text-blue-500', icon: <Clock className="w-5 h-5" /> },
  completed: { label: 'Completed', color: 'text-green-500', icon: <CheckCircle className="w-5 h-5" /> },
  failed: { label: 'Failed', color: 'text-red-500', icon: <XCircle className="w-5 h-5" /> },
};

export function ReportStatus({ reportId, onClose }: ReportStatusProps) {
  const { report, status, isLoading, error, refetch, updateStatus } = useReport(reportId);
  const [wsStatus, setWsStatus] = useState<string | null>(null);

  const handleStatusUpdate = (newStatus: ReportStatusType) => {
    if (status) {
      updateStatus({ ...status, status: newStatus });
    }
  };

  const { isConnected } = useWebSocket({
    reportId,
    onStatusUpdate: handleStatusUpdate,
    onError: (msg) => console.error('WebSocket error:', msg),
    enabled: ['analyzing', 'submitting', 'pending', 'uploading'].includes(report?.status || ''),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600">Error: {error || 'Report not found'}</p>
        {onClose && (
          <button onClick={onClose} className="mt-2 text-sm text-primary-600 hover:text-primary-700">
            Go back
          </button>
        )}
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[report.status];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Report #{report.id}</h2>
          <p className="text-sm text-gray-500 mt-1">
            Created {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected && (
            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
              Live
            </span>
          )}
          <div className={`flex items-center px-3 py-1.5 rounded-full ${statusConfig.color} bg-opacity-10`}>
            {statusConfig.icon}
            <span className="ml-2 font-medium">{statusConfig.label}</span>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {status?.progress_percent !== undefined && (
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{status.progress_percent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-primary-500 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${status.progress_percent}%` }}
            />
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {report.analysis_result && (
        <AnalysisResultsSection result={report.analysis_result} />
      )}

      {/* Geolocation */}
      {report.extracted_geolocation && (
        <GeolocationSection geo={report.extracted_geolocation} />
      )}

      {/* Media Files */}
      <MediaSection report={report} />

      {/* Complaint Reference */}
      {report.complaint_ref && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-medium text-green-900 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Complaint Filed
          </h4>
          <p className="text-green-800 mt-1">Reference: {report.complaint_ref}</p>
        </div>
      )}

      {/* Description */}
      {report.text_description && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 flex items-center mb-2">
            <FileText className="w-5 h-5 mr-2" />
            Description
          </h4>
          <p className="text-gray-700 whitespace-pre-wrap">{report.text_description}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex space-x-3">
        {report.status === 'pending' && (
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Refresh Status
          </button>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
        )}
      </div>
    </div>
  );
}

function AnalysisResultsSection({ result }: { result: AnalysisResult }) {
  return (
    <div className="p-4 bg-white border rounded-lg">
      <h4 className="font-medium text-gray-900 flex items-center mb-4">
        <Shield className="w-5 h-5 mr-2" />
        AI Analysis Results
      </h4>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Harmful Content Detected</p>
          <p className={`font-medium ${result.contains_harmful_content ? 'text-red-600' : 'text-green-600'}`}>
            {result.contains_harmful_content ? 'Yes' : 'No'}
          </p>
        </div>

        <div>
          <p className="text-sm text-gray-500">Violation Severity</p>
          <div className="flex items-center">
            <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
              <div
                className={`h-2 rounded-full ${
                  result.violation_severity >= 7 ? 'bg-red-500' :
                  result.violation_severity >= 4 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${(result.violation_severity / 10) * 100}%` }}
              />
            </div>
            <span className="font-medium">{result.violation_severity}/10</span>
          </div>
        </div>

        <div>
          <p className="text-sm text-gray-500">Recommended Action</p>
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            result.recommended_action === 'auto_submit' ? 'bg-green-100 text-green-800' :
            result.recommended_action === 'reject' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {result.recommended_action.replace('_', ' ')}
          </span>
        </div>

        <div>
          <p className="text-sm text-gray-500">Categories</p>
          <p className="font-medium text-sm">
            {result.harmful_categories.length > 0
              ? result.harmful_categories.join(', ')
              : 'None detected'}
          </p>
        </div>
      </div>
    </div>
  );
}

function GeolocationSection({ geo }: { geo: GeolocationData }) {
  return (
    <div className="p-4 bg-white border rounded-lg">
      <h4 className="font-medium text-gray-900 flex items-center mb-4">
        <MapPin className="w-5 h-5 mr-2" />
        Detected Location
      </h4>

      <div className="grid grid-cols-2 gap-4">
        {geo.address && (
          <div className="col-span-2">
            <p className="text-sm text-gray-500">Address</p>
            <p className="font-medium">{geo.address}</p>
          </div>
        )}
        {geo.city && (
          <div>
            <p className="text-sm text-gray-500">City</p>
            <p className="font-medium">{geo.city}</p>
          </div>
        )}
        {geo.country && (
          <div>
            <p className="text-sm text-gray-500">Country</p>
            <p className="font-medium">{geo.country}</p>
          </div>
        )}
        {(geo.estimated_lat !== undefined && geo.estimated_lng !== undefined) && (
          <div>
            <p className="text-sm text-gray-500">Coordinates</p>
            <p className="font-medium text-sm">
              {geo.estimated_lat.toFixed(6)}, {geo.estimated_lng.toFixed(6)}
            </p>
          </div>
        )}
        <div>
          <p className="text-sm text-gray-500">Confidence</p>
          <p className="font-medium">{Math.round(geo.confidence * 100)}%</p>
        </div>
      </div>

      {geo.landmarks && geo.landmarks.length > 0 && (
        <div className="mt-4">
          <p className="text-sm text-gray-500 mb-2">Nearby Landmarks</p>
          <div className="flex flex-wrap gap-2">
            {geo.landmarks.map((landmark, idx) => (
              <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                {landmark}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MediaSection({ report }: { report: { media_image_paths?: string[]; media_video_paths?: string[]; media_audio_path?: string } }) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const images = report.media_image_paths || [];
  const videos = report.media_video_paths || [];
  const hasAudio = !!report.media_audio_path;

  if (images.length === 0 && videos.length === 0 && !hasAudio) {
    return null;
  }

  return (
    <div className="p-4 bg-white border rounded-lg">
      <h4 className="font-medium text-gray-900 mb-4">Uploaded Media</h4>

      {/* Images */}
      {images.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-2">Images ({images.length})</p>
          <div className="grid grid-cols-4 gap-2">
            {images.map((path, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedImage(path)}
                className="aspect-square bg-gray-100 rounded-lg overflow-hidden hover:opacity-80 transition-opacity"
              >
                <img
                  src={path.startsWith('/') ? path : `/${path}`}
                  alt={`Image ${idx + 1}`}
                  className="w-full h-full object-cover"
                />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Videos */}
      {videos.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-2">Videos ({videos.length})</p>
          <div className="space-y-2">
            {videos.map((path, idx) => (
              <video
                key={idx}
                src={path.startsWith('/') ? path : `/${path}`}
                controls
                className="w-full max-h-48 rounded-lg"
              />
            ))}
          </div>
        </div>
      )}

      {/* Audio */}
      {hasAudio && (
        <div>
          <p className="text-sm text-gray-500 mb-2">Audio</p>
          <audio
            src={report.media_audio_path!.startsWith('/') ? report.media_audio_path : `/${report.media_audio_path}`}
            controls
            className="w-full"
          />
        </div>
      )}

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50"
          onClick={() => setSelectedImage(null)}
        >
          <img
            src={selectedImage.startsWith('/') ? selectedImage : `/${selectedImage}`}
            alt="Full size"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  );
}

export default ReportStatus;
