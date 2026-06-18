from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db_session
from features.sla_store.schemas import (
    LensCreateRequest,
    InventoryAddRequest,
    InventoryUpdateRequest,
    OrderStatusUpdateRequest,
    SLASetRequest,
    StoreDelaySetRequest,
    StageTimeSetRequest
)
from features.sla_store.sla_store import StoreService
from auth import get_current_admin

router = APIRouter(prefix="/api/store", tags=["Store & Settings"])

@router.post("/lens/add")
async def add_lens_type(
    request: LensCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.add_lens_type(request)

@router.post("/inventory/add")
async def add_inventory(
    request: InventoryAddRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.add_inventory(request)

@router.put("/inventory/{inventory_id}")
async def update_inventory(
    inventory_id: str,
    request: InventoryUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.update_inventory(inventory_id, request)

@router.get("/inventory/all")
async def get_all_inventory(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_all_inventory()

@router.get("/inventory/lens/{lens_type}")
async def get_inventory_by_lens(
    lens_type: str,
    lens_index: float = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_inventory_by_lens(lens_type, lens_index)

@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    request: OrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.update_order_status(order_id, request, current_user)

@router.get("/orders/all")
async def get_all_orders(
    status: str = Query(None),
    store: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_all_orders(status, store, page, limit)

@router.post("/sla/set")
async def set_sla(
    request: SLASetRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.set_sla(request, current_user)

@router.get("/sla/all")
async def get_all_sla(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_all_sla()

@router.get("/sla/{lens_type}")
async def get_sla_by_lens(
    lens_type: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_sla_by_lens(lens_type)

@router.delete("/sla/{lens_type}")
async def delete_sla(
    lens_type: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.delete_sla(lens_type)

@router.post("/store-delay/set")
async def set_store_delay(
    request: StoreDelaySetRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.set_store_delay(request, current_user)

@router.get("/store-delay/all")
async def get_all_store_delays(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_all_store_delays()

@router.delete("/store-delay/{store_location}")
async def delete_store_delay(
    store_location: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.delete_store_delay(store_location)

@router.post("/stage-time/set")
async def set_stage_time(
    request: StageTimeSetRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.set_stage_time(request, current_user)

@router.get("/stage-time/all")
async def get_all_stage_times(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.get_all_stage_times()

@router.delete("/stage-time/{stage_name}")
async def delete_stage_time(
    stage_name: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_admin)
):
    service = StoreService(db)
    return await service.delete_stage_time(stage_name)