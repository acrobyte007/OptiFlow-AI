from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PrescriptionCreate(BaseModel):
    sph: float = Field(..., ge=-20, le=20)
    cyl: Optional[float] = Field(None, ge=-10, le=10)
    axis: Optional[int] = Field(None, ge=0, le=180)
    add_power: Optional[float] = Field(None, ge=0, le=5)

class OrderCreateRequest(BaseModel):
    store_location: str = Field(..., min_length=1, max_length=100)
    lens_type: str = Field(..., min_length=1)
    lens_index: float = Field(..., ge=1.5, le=1.74)
    coating: Optional[str] = None
    frame_model: Optional[str] = None
    prescription: PrescriptionCreate

class OrderCreateResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    store_location: str
    sla_deadline: datetime
    created_at: datetime
    message: str

class OrderProgressResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    status: str
    store_location: str
    created_at: datetime
    sla_deadline: datetime
    estimated_arrival: datetime
    time_remaining_hours: float
    progress_percentage: float
    is_breached: bool
    risk_score: float
    current_stage: str
    prescription: Optional[PrescriptionCreate]
    order_lenses: List[dict]
    logs: List[dict]
    qc_records: List[dict]

class OrderListResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    status: str
    store_location: str
    created_at: datetime
    sla_deadline: datetime
    estimated_arrival: datetime
    progress_percentage: float
    is_breached: bool
    risk_score: float
    current_stage: str