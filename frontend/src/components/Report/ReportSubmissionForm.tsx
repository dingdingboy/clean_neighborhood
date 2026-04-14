import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Building, Loader2, CheckCircle } from 'lucide-react';
import { MediaDropzone } from '@/components/Upload/MediaDropzone';
import { useOffices, useReport } from '@/hooks';
import { api } from '@/services/api';
import { UploadedFile } from '@/types';

export function ReportSubmissionForm() {
  const navigate = useNavigate();
  const { offices, isLoading: officesLoading } = useOffices();
  const { createReport, submitReport } = useReport(null);

  const [selectedOffice, setSelectedOffice] = useState<number>('');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [createdReportId, setCreatedReportId] = useState<number | null>(null);

  const handleFilesSelected = (selectedFiles: UploadedFile[]) => {
    setFiles(selectedFiles);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      // Validate
      if (!selectedOffice) {
        throw new Error('Please select an office');
      }
      if (files.length === 0 && !description.trim()) {
        throw new Error('Please upload at least one file or provide a description');
      }

      // Count files by type
      const imageCount = files.filter((f) => f.type === 'image').length;
      const videoCount = files.filter((f) => f.type === 'video').length;
      const hasAudio = files.some((f) => f.type === 'audio');

      // Create report
      const uploadResponse = await createReport({
        office_id: Number(selectedOffice),
        text_description: description,
        media_summary: {
          image_count: imageCount,
          video_count: videoCount,
          has_audio: hasAudio,
          has_text: !!description.trim(),
        },
      });

      const reportId = uploadResponse.report_id;
      setCreatedReportId(reportId);

      // Upload files
      let uploadedCount = 0;
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const index = files
          .filter((f) => f.type === file.type)
          .indexOf(file);

        await api.uploadFile(
          reportId,
          file.type,
          file.file,
          index,
          (progress) => {
            setFiles((prev) =>
              prev.map((f, idx) =>
                idx === i ? { ...f, progress, uploaded: progress === 100 } : f
              )
            );
          }
        );
        uploadedCount++;
      }

      // Submit for processing
      await submitReport(reportId);

      // Navigate to report status page
      navigate(`/reports/${reportId}`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit report');
      setIsSubmitting(false);
    }
  };

  if (officesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (offices.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 bg-white rounded-xl shadow-sm">
        <Building className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No Offices Configured</h2>
        <p className="text-gray-600 mb-4">
          You need to configure at least one office before submitting reports.
        </p>
        <a
          href="/config"
          className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Configure Offices
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h1 className="text-2xl font-bold text-gray-900">Submit a Report</h1>
          <p className="text-gray-600 mt-1">
            Upload images or videos of public interest violations for AI analysis.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Office Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Building className="w-4 h-4 inline mr-1" />
              Select Office
            </label>
            <select
              value={selectedOffice}
              onChange={(e) => setSelectedOffice(Number(e.target.value))}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              required
            >
              <option value="">Choose an office...</option>
              {offices
                .filter((o) => o.is_active)
                .map((office) => (
                  <option key={office.id} value={office.id}>
                    {office.name} {office.region ? `(${office.region})` : ''}
                  </option>
                ))}
            </select>
          </div>

          {/* Media Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Upload className="w-4 h-4 inline mr-1" />
              Upload Media
            </label>
            <MediaDropzone onFilesSelected={handleFilesSelected} />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FileText className="w-4 h-4 inline mr-1" />
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              placeholder="Provide additional context about the violation..."
            />
          </div>

          {/* Error Message */}
          {submitError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{submitError}</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex items-center justify-between pt-4">
            <p className="text-sm text-gray-500">
              {files.length} file(s) selected
            </p>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center px-6 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Submit Report
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Success Modal */}
      {createdReportId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-gray-900 mb-2">Report Submitted!</h3>
            <p className="text-gray-600 mb-6">
              Your report has been created and is now being analyzed. You will be redirected to the status page.
            </p>
            <div className="animate-pulse text-sm text-gray-500">Redirecting...</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportSubmissionForm;
