// Office Types
export interface Office {
  id: number;
  name: string;
  hotline_number?: string;
  country_code: string;
  region?: string;
  address?: string;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface OfficeCreate {
  name: string;
  hotline_number?: string;
  country_code?: string;
  region?: string;
  address?: string;
  is_active?: boolean;
  priority?: number;
}

export interface OfficeUpdate extends Partial<OfficeCreate> {}

// Endpoint Types
export type EndpointType = 'web_service' | 'email' | 'api';
export type AuthType = 'none' | 'bearer' | 'api_key';

export interface Endpoint {
  id: number;
  office_id: number;
  endpoint_type: EndpointType;
  url: string;
  http_method: string;
  headers_json?: Record<string, string>;
  auth_type?: AuthType;
  auth_config?: Record<string, string>;
  payload_template?: string;
  success_criteria?: string;
  retry_policy?: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface EndpointCreate {
  office_id: number;
  endpoint_type: EndpointType;
  url: string;
  http_method?: string;
  headers_json?: Record<string, string>;
  auth_type?: AuthType;
  auth_config?: Record<string, string>;
  payload_template?: string;
  success_criteria?: string;
  retry_policy?: Record<string, unknown>;
  is_active?: boolean;
}

export interface EndpointUpdate extends Partial<EndpointCreate> {}

export interface EndpointTestRequest {
  test_payload?: Record<string, unknown>;
}

export interface EndpointTestResponse {
  success: boolean;
  status_code?: number;
  response_body?: string;
  error_message?: string;
  response_time_ms?: number;
}

// Report Types
export type ReportStatus =
  | 'pending'
  | 'uploading'
  | 'analyzing'
  | 'review_required'
  | 'approved'
  | 'rejected'
  | 'submitting'
  | 'completed'
  | 'failed';

export interface MediaSummary {
  image_count: number;
  video_count: number;
  has_audio: boolean;
  has_text: boolean;
}

export interface GeolocationData {
  confidence: number;
  country?: string;
  city?: string;
  landmarks?: string[];
  estimated_lat?: number;
  estimated_lng?: number;
  address?: string;
}

export interface AnalysisResult {
  contains_harmful_content: boolean;
  harmful_categories: string[];
  geolocation?: GeolocationData;
  violation_severity: number;
  recommended_action: 'auto_submit' | 'review' | 'reject';
  raw_analysis?: Record<string, unknown>;
}

export interface Report {
  id: number;
  office_id: number;
  status: ReportStatus;
  media_image_paths?: string[];
  media_video_paths?: string[];
  media_audio_path?: string;
  text_description?: string;
  analysis_result?: AnalysisResult;
  detected_categories?: string[];
  confidence_scores?: Record<string, number>;
  extracted_geolocation?: GeolocationData;
  geolocation_source?: string;
  complaint_ref?: string;
  submitted_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ReportCreate {
  office_id: number;
  text_description?: string;
  media_summary?: MediaSummary;
}

export interface UploadUrlInfo {
  field_name: string;
  url: string;
  method: string;
  max_size: number;
  expires_at: string;
}

export interface UploadUrlResponse {
  report_id: number;
  upload_urls: UploadUrlInfo[];
  websocket_url: string;
}

export interface ReportStatusResponse {
  id: number;
  status: ReportStatus;
  progress_percent?: number;
  current_step?: string;
  estimated_completion?: string;
  created_at: string;
  updated_at: string;
}

export interface UploadedFile {
  file: File;
  type: 'image' | 'video' | 'audio';
  preview?: string;
  progress: number;
  uploaded: boolean;
  error?: string;
}
