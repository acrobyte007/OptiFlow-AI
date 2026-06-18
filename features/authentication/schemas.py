from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    STORE_MANAGER = "STORE_MANAGER"
    QC_INSPECTOR = "QC_INSPECTOR"
    WAREHOUSE = "WAREHOUSE"
    SUPPORT = "SUPPORT"
    CUSTOMER = "CUSTOMER"

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.CUSTOMER
    store_location: Optional[str] = None
    admin_secret: Optional[str] = None

class UserRegisterResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    store_location: Optional[str]
    is_active: bool
    created_at: datetime

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRegisterResponse