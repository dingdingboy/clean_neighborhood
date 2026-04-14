from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import ConfigOffice, ConfigEndpoint
from app.schemas.config import (
    OfficeCreate,
    OfficeUpdate,
    OfficeResponse,
    EndpointCreate,
    EndpointUpdate,
    EndpointResponse,
    EndpointTestRequest,
    EndpointTestResponse,
)
from app.services.complaint_service import ComplaintService

router = APIRouter()


# Office endpoints
@router.get("/offices", response_model=List[OfficeResponse])
async def list_offices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all configured offices."""
    result = await db.execute(select(ConfigOffice).offset(skip).limit(limit))
    offices = result.scalars().all()
    return offices


@router.post("/offices", response_model=OfficeResponse, status_code=status.HTTP_201_CREATED)
async def create_office(
    office: OfficeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new office configuration."""
    db_office = ConfigOffice(**office.model_dump())
    db.add(db_office)
    await db.flush()
    await db.refresh(db_office)
    return db_office


@router.get("/offices/{office_id}", response_model=OfficeResponse)
async def get_office(
    office_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific office by ID."""
    result = await db.execute(
        select(ConfigOffice).where(ConfigOffice.id == office_id)
    )
    office = result.scalar_one_or_none()
    if not office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Office {office_id} not found",
        )
    return office


@router.put("/offices/{office_id}", response_model=OfficeResponse)
async def update_office(
    office_id: int,
    office_update: OfficeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing office configuration."""
    result = await db.execute(
        select(ConfigOffice).where(ConfigOffice.id == office_id)
    )
    office = result.scalar_one_or_none()
    if not office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Office {office_id} not found",
        )

    update_data = office_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(office, field, value)

    await db.flush()
    await db.refresh(office)
    return office


@router.delete("/offices/{office_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_office(
    office_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an office configuration."""
    result = await db.execute(
        select(ConfigOffice).where(ConfigOffice.id == office_id)
    )
    office = result.scalar_one_or_none()
    if not office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Office {office_id} not found",
        )

    await db.delete(office)
    return None


# Endpoint endpoints
@router.get("/endpoints", response_model=List[EndpointResponse])
async def list_endpoints(
    office_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all configured endpoints, optionally filtered by office."""
    query = select(ConfigEndpoint)
    if office_id:
        query = query.where(ConfigEndpoint.office_id == office_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    endpoints = result.scalars().all()
    return endpoints


@router.post("/endpoints", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    endpoint: EndpointCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new endpoint configuration."""
    db_endpoint = ConfigEndpoint(**endpoint.model_dump())
    db.add(db_endpoint)
    await db.flush()
    await db.refresh(db_endpoint)
    return db_endpoint


@router.get("/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific endpoint by ID."""
    result = await db.execute(
        select(ConfigEndpoint).where(ConfigEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint {endpoint_id} not found",
        )
    return endpoint


@router.put("/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(
    endpoint_id: int,
    endpoint_update: EndpointUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing endpoint configuration."""
    result = await db.execute(
        select(ConfigEndpoint).where(ConfigEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint {endpoint_id} not found",
        )

    update_data = endpoint_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(endpoint, field, value)

    await db.flush()
    await db.refresh(endpoint)
    return endpoint


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an endpoint configuration."""
    result = await db.execute(
        select(ConfigEndpoint).where(ConfigEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint {endpoint_id} not found",
        )

    await db.delete(endpoint)
    return None


@router.post("/endpoints/{endpoint_id}/test", response_model=EndpointTestResponse)
async def test_endpoint(
    endpoint_id: int,
    test_request: EndpointTestRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Test an endpoint connectivity and configuration."""
    result = await db.execute(
        select(ConfigEndpoint).where(ConfigEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint {endpoint_id} not found",
        )

    service = ComplaintService(db)
    test_result = await service.test_endpoint(
        endpoint=endpoint,
        test_payload=test_request.test_payload if test_request else None,
    )
    return test_result
