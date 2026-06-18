from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db_session
from features.authentication.schemas import UserRegisterRequest, UserLoginRequest
from features.authentication.user_service import UserService
from auth import get_current_user

user_router = APIRouter(prefix="/api/user", tags=["User"])

@user_router.post("/register")
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session)
):
    service = UserService(db)
    return await service.register_user(request)

@user_router.post("/login")
async def login_user(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    service = UserService(db)
    return await service.login_user(request)

@user_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information from JWT token.
    NO database lookup - purely from decoded token.
    """
    return current_user