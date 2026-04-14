import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Phone, Globe, TestTube, CheckCircle, XCircle } from 'lucide-react';
import { useOffices, useEndpoints } from '@/hooks';
import { Office, OfficeCreate, Endpoint, EndpointCreate, AuthType, EndpointType } from '@/types';

export function OfficeConfig() {
  const { offices, isLoading, error, createOffice, updateOffice, deleteOffice, refetch } = useOffices();
  const [showOfficeForm, setShowOfficeForm] = useState(false);
  const [editingOffice, setEditingOffice] = useState<Office | null>(null);
  const [selectedOffice, setSelectedOffice] = useState<Office | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600">Error: {error}</p>
        <button
          onClick={refetch}
          className="mt-2 text-sm text-primary-600 hover:text-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Office Configuration</h2>
        <button
          onClick={() => {
            setEditingOffice(null);
            setShowOfficeForm(true);
          }}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Office
        </button>
      </div>

      {/* Office List */}
      <div className="grid gap-4">
        {offices.map((office) => (
          <OfficeCard
            key={office.id}
            office={office}
            onEdit={() => {
              setEditingOffice(office);
              setShowOfficeForm(true);
            }}
            onDelete={() => deleteOffice(office.id)}
            onSelect={() => setSelectedOffice(office.id === selectedOffice?.id ? null : office)}
            isSelected={selectedOffice?.id === office.id}
          />
        ))}

        {offices.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <p className="text-gray-500">No offices configured yet.</p>
            <p className="text-sm text-gray-400 mt-1">
              Add an office to start receiving reports.
            </p>
          </div>
        )}
      </div>

      {/* Office Form Modal */}
      {showOfficeForm && (
        <OfficeFormModal
          office={editingOffice}
          onClose={() => setShowOfficeForm(false)}
          onSubmit={async (data) => {
            if (editingOffice) {
              await updateOffice(editingOffice.id, data);
            } else {
              await createOffice(data);
            }
            setShowOfficeForm(false);
          }}
        />
      )}

      {/* Endpoints Section */}
      {selectedOffice && (
        <EndpointsSection office={selectedOffice} />
      )}
    </div>
  );
}

function OfficeCard({
  office,
  onEdit,
  onDelete,
  onSelect,
  isSelected,
}: {
  office: Office;
  onEdit: () => void;
  onDelete: () => void;
  onSelect: () => void;
  isSelected: boolean;
}) {
  return (
    <div
      className={`p-4 border rounded-lg transition-colors cursor-pointer ${
        isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{office.name}</h3>
          {office.region && (
            <p className="text-sm text-gray-500">{office.region}</p>
          )}
          {office.hotline_number && (
            <div className="flex items-center mt-2 text-sm text-gray-600">
              <Phone className="w-4 h-4 mr-1" />
              {office.hotline_number}
            </div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-2 py-1 text-xs font-medium rounded-full ${
              office.is_active
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {office.is_active ? 'Active' : 'Inactive'}
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('Are you sure you want to delete this office?')) {
                onDelete();
              }
            }}
            className="p-2 text-gray-400 hover:text-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function OfficeFormModal({
  office,
  onClose,
  onSubmit,
}: {
  office: Office | null;
  onClose: () => void;
  onSubmit: (data: OfficeCreate) => void;
}) {
  const [formData, setFormData] = useState<OfficeCreate>({
    name: office?.name || '',
    hotline_number: office?.hotline_number || '',
    country_code: office?.country_code || 'US',
    region: office?.region || '',
    address: office?.address || '',
    is_active: office?.is_active ?? true,
    priority: office?.priority || 100,
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg">
        <h3 className="text-xl font-bold mb-4">
          {office ? 'Edit Office' : 'Add Office'}
        </h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(formData);
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Hotline Number</label>
            <input
              type="text"
              value={formData.hotline_number}
              onChange={(e) => setFormData({ ...formData, hotline_number: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              placeholder="+1-800-XXX-XXXX"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Country Code</label>
              <input
                type="text"
                value={formData.country_code}
                onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Region</label>
              <input
                type="text"
                value={formData.region}
                onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Address</label>
            <textarea
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              rows={2}
            />
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">Active</label>
          </div>
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              {office ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EndpointsSection({ office }: { office: Office }) {
  const { endpoints, isLoading, createEndpoint, deleteEndpoint, testEndpoint } = useEndpoints(office.id);
  const [showForm, setShowForm] = useState(false);
  const [testResult, setTestResult] = useState<{ endpointId: number; result: { success: boolean; message: string } } | null>(null);

  const handleTest = async (endpointId: number) => {
    try {
      const result = await testEndpoint(endpointId);
      setTestResult({
        endpointId,
        result: {
          success: result.success,
          message: result.success
            ? `Success! (${result.response_time_ms}ms)`
            : result.error_message || 'Test failed',
        },
      });
    } catch (err) {
      setTestResult({
        endpointId,
        result: {
          success: false,
          message: err instanceof Error ? err.message : 'Test failed',
        },
      });
    }
  };

  return (
    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Endpoints for {office.name}
        </h3>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          <Plus className="w-4 h-4 mr-1" />
          Add Endpoint
        </button>
      </div>

      {endpoints.map((endpoint) => (
        <div key={endpoint.id} className="mb-3 p-3 bg-white rounded border">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center">
                <Globe className="w-4 h-4 text-gray-400 mr-2" />
                <span className="font-medium">{endpoint.endpoint_type}</span>
                <span className="mx-2 text-gray-300">|</span>
                <span className="text-sm text-gray-600">{endpoint.http_method}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1 truncate">{endpoint.url}</p>
              {testResult?.endpointId === endpoint.id && (
                <div className={`flex items-center mt-2 text-sm ${testResult.result.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testResult.result.success ? (
                    <CheckCircle className="w-4 h-4 mr-1" />
                  ) : (
                    <XCircle className="w-4 h-4 mr-1" />
                  )}
                  {testResult.result.message}
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleTest(endpoint.id)}
                className="p-1.5 text-gray-400 hover:text-blue-600"
                title="Test endpoint"
              >
                <TestTube className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm('Delete this endpoint?')) {
                    deleteEndpoint(endpoint.id);
                  }
                }}
                className="p-1.5 text-gray-400 hover:text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ))}

      {endpoints.length === 0 && (
        <p className="text-sm text-gray-500">No endpoints configured for this office.</p>
      )}

      {showForm && (
        <EndpointFormModal
          officeId={office.id}
          onClose={() => setShowForm(false)}
          onSubmit={async (data) => {
            await createEndpoint(data);
            setShowForm(false);
          }}
        />
      )}
    </div>
  );
}

function EndpointFormModal({
  officeId,
  onClose,
  onSubmit,
}: {
  officeId: number;
  onClose: () => void;
  onSubmit: (data: EndpointCreate) => void;
}) {
  const [formData, setFormData] = useState<EndpointCreate>({
    office_id: officeId,
    endpoint_type: 'web_service',
    url: '',
    http_method: 'POST',
    auth_type: 'none',
    auth_config: {},
    headers_json: {},
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg">
        <h3 className="text-xl font-bold mb-4">Add Endpoint</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(formData);
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700">Type</label>
            <select
              value={formData.endpoint_type}
              onChange={(e) => setFormData({ ...formData, endpoint_type: e.target.value as EndpointType })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="web_service">Web Service</option>
              <option value="api">API</option>
              <option value="email">Email</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">URL</label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              required
              placeholder="https://api.example.com/complaints"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">HTTP Method</label>
            <select
              value={formData.http_method}
              onChange={(e) => setFormData({ ...formData, http_method: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="GET">GET</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Authentication</label>
            <select
              value={formData.auth_type}
              onChange={(e) => setFormData({ ...formData, auth_type: e.target.value as AuthType })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="none">None</option>
              <option value="bearer">Bearer Token</option>
              <option value="api_key">API Key</option>
            </select>
          </div>
          {formData.auth_type === 'bearer' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Bearer Token</label>
              <input
                type="password"
                onChange={(e) => setFormData({
                  ...formData,
                  auth_config: { ...formData.auth_config, token: e.target.value }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                placeholder="eyJhbGciOiJIUzI1NiIs..."
              />
            </div>
          )}
          {formData.auth_type === 'api_key' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">API Key Name</label>
                <input
                  type="text"
                  defaultValue={formData.auth_config?.key_name || 'X-API-Key'}
                  onChange={(e) => setFormData({
                    ...formData,
                    auth_config: { ...formData.auth_config, key_name: e.target.value }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  placeholder="X-API-Key"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">API Key Value</label>
                <input
                  type="password"
                  onChange={(e) => setFormData({
                    ...formData,
                    auth_config: { ...formData.auth_config, key_value: e.target.value }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
            </>
          )}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
