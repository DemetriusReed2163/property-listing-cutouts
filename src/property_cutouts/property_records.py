from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RecordKind(StrEnum):
    LISTING_PHOTO = "listing_photo"
    MAINTENANCE_REQUEST = "maintenance_request"
    TENANT_DOCUMENT = "tenant_document"
    INSPECTION_REMINDER = "inspection_reminder"


class MaintenanceRequest(BaseModel):
    request_id: str
    property_id: str
    summary: str
    reported_at: datetime


class TenantDocument(BaseModel):
    document_id: str
    property_id: str
    document_type: str
    received_on: date


class InspectionReminder(BaseModel):
    reminder_id: str
    property_id: str
    due_on: date
    area: str


class ListingPhotoRequest(BaseModel):
    property_id: str = Field(min_length=1)
    photo_id: str = Field(min_length=1)
    kind: RecordKind
    output_format: str = "png"


class CutoutResult(BaseModel):
    property_id: str
    photo_id: str
    status: str
    image: object
    metadata: dict[str, object] | None = None


def accepts_background_removal(request: ListingPhotoRequest) -> bool:
    return request.kind is RecordKind.LISTING_PHOTO

