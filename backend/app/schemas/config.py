from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


# Office schemas
class OfficeBase(BaseModel):
    """Base schema for office configuration."""

    name: str = Field(..., min_length=1, max_length=255)
    hotline_number: Optional[str] = Field(None, max_length=50)
    country_code: str = Field(default="US", max_length=10)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_active: bool = True
    priority: int = Field(default=100, ge=1)


class OfficeCreate(OfficeBase):
    """Schema for creating a new office."""

    pass


class OfficeUpdate(BaseModel):
    """Schema for updating an office."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hotline_number: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, max_length=10)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1)


class OfficeResponse(OfficeBase):
    """Schema for office response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Endpoint schemas
class EndpointBase(BaseModel):
    """Base schema for endpoint configuration."""

    office_id: int
    endpoint_type: str = Field(..., pattern=r"^(web_service|email|api)$")
    url: str = Field(..., max_length=2048)
    http_method: str = Field(default="POST", pattern=r"^(GET|POST|PUT|PATCH|DELETE)$")
    headers_json: Optional[Dict[str, Any]] = None
    auth_type: Optional[str] = Field(None, pattern=r"^(none|bearer|api_key)$")
    auth_config: Optional[Dict[str, Any]] = None
    payload_template: Optional[str] = None
    success_criteria: Optional[str] = None
    retry_policy: Optional[Dict[str, Any]] = None
    is_active: bool = True


class EndpointCreate(EndpointBase):
    """Schema for creating a new endpoint."""

    pass


class EndpointUpdate(BaseModel):
    """Schema for updating an endpoint."""

    office_id: Optional[int] = None
    endpoint_type: Optional[str] = Field(None, pattern=r"^(web_service|email|api)$")
    url: Optional[str] = Field(None, max_length=2048)
    http_method: Optional[str] = Field(None, pattern=r"^(GET|POST|PUT|PATCH|DELETE)$")
    headers_json: Optional[Dict[str, Any]] = None
    auth_type: Optional[str] = Field(None, pattern=r"^(none|bearer|api_key)$")
    auth_config: Optional[Dict[str, Any]] = None
    payload_template: Optional[str] = None
    success_criteria: Optional[str] = None
    retry_policy: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EndpointResponse(EndpointBase):
    """Schema for endpoint response."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EndpointTestRequest(BaseModel):
    """Schema for testing an endpoint."""

    test_payload: Optional[Dict[str, Any]] = None


class EndpointTestResponse(BaseModel):
    """Schema for endpoint test response."""

    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None
