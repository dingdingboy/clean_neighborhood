import { useState, useCallback, useEffect } from 'react';
import { api } from '@/services/api';
import { Office, OfficeCreate, OfficeUpdate, Endpoint, EndpointCreate, EndpointUpdate } from '@/types';

export function useOffices() {
  const [offices, setOffices] = useState<Office[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOffices = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listOffices();
      setOffices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch offices');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOffices();
  }, [fetchOffices]);

  const createOffice = useCallback(async (office: OfficeCreate) => {
    setIsLoading(true);
    try {
      const newOffice = await api.createOffice(office);
      setOffices((prev) => [...prev, newOffice]);
      return newOffice;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create office');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateOffice = useCallback(async (id: number, office: OfficeUpdate) => {
    setIsLoading(true);
    try {
      const updated = await api.updateOffice(id, office);
      setOffices((prev) =>
        prev.map((o) => (o.id === id ? updated : o))
      );
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update office');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteOffice = useCallback(async (id: number) => {
    setIsLoading(true);
    try {
      await api.deleteOffice(id);
      setOffices((prev) => prev.filter((o) => o.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete office');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    offices,
    isLoading,
    error,
    refetch: fetchOffices,
    createOffice,
    updateOffice,
    deleteOffice,
  };
}

export function useEndpoints(officeId?: number) {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEndpoints = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listEndpoints(officeId);
      setEndpoints(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch endpoints');
    } finally {
      setIsLoading(false);
    }
  }, [officeId]);

  useEffect(() => {
    fetchEndpoints();
  }, [fetchEndpoints]);

  const createEndpoint = useCallback(async (endpoint: EndpointCreate) => {
    setIsLoading(true);
    try {
      const newEndpoint = await api.createEndpoint(endpoint);
      setEndpoints((prev) => [...prev, newEndpoint]);
      return newEndpoint;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create endpoint');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateEndpoint = useCallback(async (id: number, endpoint: EndpointUpdate) => {
    setIsLoading(true);
    try {
      const updated = await api.updateEndpoint(id, endpoint);
      setEndpoints((prev) =>
        prev.map((e) => (e.id === id ? updated : e))
      );
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update endpoint');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteEndpoint = useCallback(async (id: number) => {
    setIsLoading(true);
    try {
      await api.deleteEndpoint(id);
      setEndpoints((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete endpoint');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const testEndpoint = useCallback(async (id: number) => {
    setIsLoading(true);
    try {
      const result = await api.testEndpoint(id);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to test endpoint');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    endpoints,
    isLoading,
    error,
    refetch: fetchEndpoints,
    createEndpoint,
    updateEndpoint,
    deleteEndpoint,
    testEndpoint,
  };
}
