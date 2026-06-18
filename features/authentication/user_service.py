import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from database.model import User
from features.authentication.schemas import UserRole
from auth import get_password_hash, verify_password, create_access_token
import dotenv
dotenv.load_dotenv()
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")
class UserService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, request_data):
        result = await self.db.execute(select(User).where(User.email == request_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        role = request_data.role
        
        if role == UserRole.ADMIN:
            admin_secret = request_data.admin_secret if hasattr(request_data, 'admin_secret') else None
            
            if not admin_secret:
                raise HTTPException(status_code=403, detail="Admin secret key required for admin registration")
            
            if admin_secret != ADMIN_SECRET_KEY:
                raise HTTPException(status_code=403, detail="Invalid admin secret key")
        
        user = User(
            name=request_data.name,
            email=request_data.email,
            password_hash=get_password_hash(request_data.password),
            role=UserRole(role),
            store_location=request_data.store_location,
            is_active=True
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        token_data = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "store_location": user.store_location
        }
        
        is_admin = user.role.value == "ADMIN"
        access_token = create_access_token(token_data, is_admin)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "store_location": user.store_location,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
        }
    async def login_user(self, login_data):
        # Find user
        result = await self.db.execute(select(User).where(User.email == login_data.email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Generate token with ALL user info
        token_data = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "store_location": user.store_location
        }
        
        is_admin = user.role.value == "ADMIN"
        access_token = create_access_token(token_data, is_admin)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "store_location": user.store_location,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
        }