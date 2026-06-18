from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db_session
from features.order_service.schemas import OrderCreateRequest, OrderCreateResponse
from features.order_service.order_service import OrderService
from auth import get_current_user, get_current_admin
from logger.logger import get_logger, log_info, log_error, log_exception
logger = get_logger(__name__)
router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("/create", response_model=OrderCreateResponse)
async def create_order(
    request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    service = OrderService(db)
    result = await service.create_order(request, current_user)
    
    return OrderCreateResponse(
        id=result["id"],
        customer_id=result["customer_id"],
        status=result["status"],
        store_location=result["store_location"],
        sla_deadline=result["sla_deadline"],
        created_at=result["created_at"],
        message=result["message"]
    )


@router.get("/my")
async def get_my_orders(
    status: str = Query(None, description="Filter by status: PLACED, PROCESSING, QC, DISPATCHED, DELIVERED"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):  
    logger.info(f"User {current_user['id']} is getting their orders")
    service = OrderService(db)
    return await service.get_customer_orders(status, page, limit, current_user)

@router.get("/{order_id}")
async def get_order_by_id(
    order_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    service = OrderService(db)
    return await service.get_order_by_id(order_id, current_user)


@router.get("/admin/all")
async def admin_get_all_orders(
    status: str = Query(None, description="Filter by status"),
    store: str = Query(None, description="Filter by store location"),
    customer_id: str = Query(None, description="Filter by customer ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = OrderService(db)
    return await service.get_all_orders_admin(status, store, customer_id, page, limit)