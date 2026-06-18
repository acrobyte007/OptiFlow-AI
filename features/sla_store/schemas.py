from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class LensCreateRequest(BaseModel):
    type: str = Field(..., min_length=1)
    index: float = Field(..., ge=1.5, le=1.74)
    coating: Optional[str] = None

class LensCreateResponse(BaseModel):
    id: str
    type: str
    index: float
    coating: Optional[str]
    message: str

class InventoryAddRequest(BaseModel):
    lens_type: str = Field(..., min_length=1)
    lens_index: float = Field(..., ge=1.5, le=1.74)
    coating: Optional[str] = None
    power: float = Field(..., ge=-20, le=20)
    quantity: int = Field(..., ge=1)
    location: str = Field(..., min_length=1)
    source: str = "IN_HOUSE"
    lead_time_hours: int = 0

class InventoryAddResponse(BaseModel):
    message: str
    lens_id: str
    inventory_id: str

class InventoryUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=0)
    location: Optional[str] = None
    lead_time_hours: Optional[int] = None

class InventoryUpdateResponse(BaseModel):
    message: str
    inventory_id: str
    quantity: int

class InventoryItemResponse(BaseModel):
    id: str
    lens_type: str
    lens_index: float
    coating: Optional[str]
    power: float
    quantity: int
    location: str
    source: str
    lead_time_hours: int

class OrderStatusUpdateRequest(BaseModel):
    status: str
    delay_reason: Optional[str] = None

class OrderStatusUpdateResponse(BaseModel):
    order_id: str
    previous_status: str
    new_status: str
    updated_at: datetime
    delay_reason: Optional[str]

class OrderListResponse(BaseModel):
    id: str
    customer_name: str
    status: str
    store_location: str
    sla_deadline: datetime
    created_at: datetime
    is_breached: bool

class SLASetRequest(BaseModel):
    lens_type: str = Field(..., min_length=1)
    sla_hours: int = Field(..., ge=1, le=720)
    complexity_factor: float = Field(1.0, ge=0.5, le=3.0)
    store_delay_hours: int = Field(0, ge=0, le=168)

class SLAResponse(BaseModel):
    id: str
    lens_type: str
    sla_hours: int
    complexity_factor: float
    store_delay_hours: int
    updated_at: datetime

class StoreDelaySetRequest(BaseModel):
    store_location: str = Field(..., min_length=1)
    delay_hours: int = Field(..., ge=0, le=168)

class StoreDelayResponse(BaseModel):
    id: str
    store_location: str
    delay_hours: int
    updated_at: datetime

class StageTimeSetRequest(BaseModel):
    stage_name: str = Field(..., min_length=1)
    default_hours: int = Field(..., ge=0, le=168)

class StageTimeResponse(BaseModel):
    id: str
    stage_name: str
    default_hours: int
    updated_at: datetime