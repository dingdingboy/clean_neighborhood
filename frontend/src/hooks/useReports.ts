import { useState, useCallback, useEffect } from 'react';
import { api } from '@/services/api';
import { Report, ReportCreate, ReportStatusResponse } from '@/types';

export function useReports(officeId?: number, status?: string) {
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listReports(officeId, status);
      setReports(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reports');
    } finally {
      setIsLoading(false);
    }
  }, [officeId, status]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const refetch = useCallback(() => {
    fetchReports();
  }, [fetchReports]);

  return { reports, isLoading, error, refetch };
}

export function useReport(reportId: number | null) {
  const [report, setReport] = useState<Report | null>(null);
  const [status, setStatus] = useState<ReportStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = useCallback(async () => {
    if (!reportId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [reportData, statusData] = await Promise.all([
        api.getReport(reportId),
        api.getReportStatus(reportId),
      ]);
      setReport(reportData);
      setStatus(statusData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report');
    } finally {
      setIsLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const createReport = useCallback(async (data: ReportCreate) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.createReport(data);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create report');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const submitReport = useCallback(async (id: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.submitReport(id);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit report');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteReport = useCallback(async (id: number) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.deleteReport(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete report');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateStatus = useCallback((newStatus: ReportStatusResponse) => {
    setStatus(newStatus);
    if (report) {
      setReport({ ...report, status: newStatus.status });
    }
  }, [report]);

  return {
    report,
    status,
    isLoading,
    error,
    refetch: fetchReport,
    createReport,
    submitReport,
    deleteReport,
    updateStatus,
  };
}
