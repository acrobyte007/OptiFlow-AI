from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException
from datetime import datetime
from database.model import Lens, Inventory, Order, OrderLog, OrderStatus, Customer, SLAConfig, StoreDelayConfig, StageTimeConfig
from features.sla_store.schemas import (
    LensCreateRequest,
    InventoryAddRequest,
    InventoryUpdateRequest,
    OrderStatusUpdateRequest,
    SLASetRequest,
    StoreDelaySetRequest,
    StageTimeSetRequest
)

class StoreService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_lens_type(self, request_data: LensCreateRequest):
        result = await self.db.execute(
            select(Lens).where(
                and_(
                    Lens.type == request_data.type,
                    Lens.index == request_data.index,
                    Lens.coating == request_data.coating
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Lens type already exists")
        
        lens = Lens(
            type=request_data.type,
            index=request_data.index,
            coating=request_data.coating
        )
        self.db.add(lens)
        await self.db.commit()
        await self.db.refresh(lens)
        
        return {
            "id": lens.id,
            "type": lens.type,
            "index": lens.index,
            "coating": lens.coating,
            "message": "Lens type added successfully"
        }
    
    async def add_inventory(self, request_data: InventoryAddRequest):
        lens_result = await self.db.execute(
            select(Lens).where(
                and_(
                    Lens.type == request_data.lens_type,
                    Lens.index == request_data.lens_index,
                    Lens.coating == request_data.coating
                )
            )
        )
        lens = lens_result.scalar_one_or_none()
        
        if not lens:
            lens = Lens(
                type=request_data.lens_type,
                index=request_data.lens_index,
                coating=request_data.coating
            )
            self.db.add(lens)
            await self.db.flush()
        
        inventory_result = await self.db.execute(
            select(Inventory).where(
                and_(
                    Inventory.lens_id == lens.id,
                    Inventory.power == request_data.power,
                    Inventory.location == request_data.location
                )
            )
        )
        inventory = inventory_result.scalar_one_or_none()
        
        if inventory:
            inventory.quantity += request_data.quantity
        else:
            inventory = Inventory(
                lens_id=lens.id,
                power=request_data.power,
                quantity=request_data.quantity,
                location=request_data.location,
                source=request_data.source,
                lead_time_hours=request_data.lead_time_hours
            )
            self.db.add(inventory)
        
        await self.db.commit()
        
        return {
            "message": f"Added {request_data.quantity} units to inventory",
            "lens_id": lens.id,
            "inventory_id": inventory.id
        }
    
    async def update_inventory(self, inventory_id: str, request_data: InventoryUpdateRequest):
        result = await self.db.execute(select(Inventory).where(Inventory.id == inventory_id))
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")
        
        if request_data.quantity is not None:
            inventory.quantity = request_data.quantity
        
        if request_data.location is not None:
            inventory.location = request_data.location
        
        if request_data.lead_time_hours is not None:
            inventory.lead_time_hours = request_data.lead_time_hours
        
        await self.db.commit()
        
        return {
            "message": "Inventory updated successfully",
            "inventory_id": inventory.id,
            "quantity": inventory.quantity
        }
    
    async def get_all_inventory(self):
        result = await self.db.execute(
            select(Inventory, Lens)
            .join(Lens, Inventory.lens_id == Lens.id)
        )
        items = result.all()
        
        return [
            {
                "id": inv.id,
                "lens_type": lens.type,
                "lens_index": lens.index,
                "coating": lens.coating,
                "power": inv.power,
                "quantity": inv.quantity,
                "location": inv.location,
                "source": inv.source,
                "lead_time_hours": inv.lead_time_hours
            }
            for inv, lens in items
        ]
    
    async def get_inventory_by_lens(self, lens_type: str, lens_index: float = None):
        query = select(Inventory, Lens).join(Lens, Inventory.lens_id == Lens.id)
        query = query.where(Lens.type == lens_type)
        
        if lens_index:
            query = query.where(Lens.index == lens_index)
        
        result = await self.db.execute(query)
        items = result.all()
        
        return [
            {
                "id": inv.id,
                "lens_type": lens.type,
                "lens_index": lens.index,
                "coating": lens.coating,
                "power": inv.power,
                "quantity": inv.quantity,
                "location": inv.location
            }
            for inv, lens in items
        ]
    
    async def update_order_status(self, order_id: str, request_data: OrderStatusUpdateRequest, current_user: dict):
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        previous_status = order.status.value
        order.status = OrderStatus(request_data.status)
        
        if request_data.status == "DELIVERED":
            order.completed_at = datetime.now()
        
        await self.db.commit()
        
        log = OrderLog(
            order_id=order_id,
            status=OrderStatus(request_data.status),
            performed_by_id=current_user.get("id"),
            delay_reason=request_data.delay_reason
        )
        self.db.add(log)
        await self.db.commit()
        
        return {
            "order_id": order.id,
            "previous_status": previous_status,
            "new_status": order.status.value,
            "updated_at": datetime.now(),
            "delay_reason": request_data.delay_reason
        }
    
    async def get_all_orders(self, status: str = None, store: str = None, page: int = 1, limit: int = 20):
        query = select(Order)
        
        if status:
            query = query.where(Order.status == status)
        if store:
            query = query.where(Order.store_location == store)
        
        count_query = select(func.count()).select_from(Order)
        if status:
            count_query = count_query.where(Order.status == status)
        if store:
            count_query = count_query.where(Order.store_location == store)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        order_list = []
        for order in orders:
            customer_result = await self.db.execute(
                select(Customer).where(Customer.id == order.customer_id)
            )
            customer = customer_result.scalar_one_or_none()
            
            order_list.append({
                "id": order.id,
                "customer_name": customer.name if customer else "Unknown",
                "status": order.status.value,
                "store_location": order.store_location,
                "sla_deadline": order.sla_deadline,
                "created_at": order.created_at,
                "is_breached": order.is_breached
            })
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "orders": order_list
        }
    
    async def set_sla(self, request_data: SLASetRequest, current_user: dict):
        result = await self.db.execute(
            select(SLAConfig).where(SLAConfig.lens_type == request_data.lens_type)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.sla_hours = request_data.sla_hours
            config.complexity_factor = request_data.complexity_factor
            config.store_delay_hours = request_data.store_delay_hours
            config.updated_by = current_user.get("id")
        else:
            config = SLAConfig(
                lens_type=request_data.lens_type,
                sla_hours=request_data.sla_hours,
                complexity_factor=request_data.complexity_factor,
                store_delay_hours=request_data.store_delay_hours,
                updated_by=current_user.get("id")
            )
            self.db.add(config)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return {
            "id": config.id,
            "lens_type": config.lens_type,
            "sla_hours": config.sla_hours,
            "complexity_factor": config.complexity_factor,
            "store_delay_hours": config.store_delay_hours,
            "updated_at": config.updated_at
        }
    
    async def get_all_sla(self):
        result = await self.db.execute(select(SLAConfig))
        configs = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "lens_type": c.lens_type,
                "sla_hours": c.sla_hours,
                "complexity_factor": c.complexity_factor,
                "store_delay_hours": c.store_delay_hours,
                "updated_at": c.updated_at
            }
            for c in configs
        ]
    
    async def get_sla_by_lens(self, lens_type: str):
        result = await self.db.execute(
            select(SLAConfig).where(SLAConfig.lens_type == lens_type)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="SLA config not found")
        
        return {
            "id": config.id,
            "lens_type": config.lens_type,
            "sla_hours": config.sla_hours,
            "complexity_factor": config.complexity_factor,
            "store_delay_hours": config.store_delay_hours,
            "updated_at": config.updated_at
        }
    
    async def delete_sla(self, lens_type: str):
        result = await self.db.execute(
            select(SLAConfig).where(SLAConfig.lens_type == lens_type)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="SLA config not found")
        
        await self.db.delete(config)
        await self.db.commit()
        
        return {"message": f"SLA config for {lens_type} deleted successfully"}
    
    async def set_store_delay(self, request_data: StoreDelaySetRequest, current_user: dict):
        result = await self.db.execute(
            select(StoreDelayConfig).where(StoreDelayConfig.store_location == request_data.store_location)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.delay_hours = request_data.delay_hours
            config.updated_by = current_user.get("id")
        else:
            config = StoreDelayConfig(
                store_location=request_data.store_location,
                delay_hours=request_data.delay_hours,
                updated_by=current_user.get("id")
            )
            self.db.add(config)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return {
            "id": config.id,
            "store_location": config.store_location,
            "delay_hours": config.delay_hours,
            "updated_at": config.updated_at
        }
    
    async def get_all_store_delays(self):
        result = await self.db.execute(select(StoreDelayConfig))
        configs = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "store_location": c.store_location,
                "delay_hours": c.delay_hours,
                "updated_at": c.updated_at
            }
            for c in configs
        ]
    
    async def delete_store_delay(self, store_location: str):
        result = await self.db.execute(
            select(StoreDelayConfig).where(StoreDelayConfig.store_location == store_location)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Store delay config not found")
        
        await self.db.delete(config)
        await self.db.commit()
        
        return {"message": f"Store delay for {store_location} deleted successfully"}
    
    async def set_stage_time(self, request_data: StageTimeSetRequest, current_user: dict):
        result = await self.db.execute(
            select(StageTimeConfig).where(StageTimeConfig.stage_name == request_data.stage_name)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.default_hours = request_data.default_hours
            config.updated_by = current_user.get("id")
        else:
            config = StageTimeConfig(
                stage_name=request_data.stage_name,
                default_hours=request_data.default_hours,
                updated_by=current_user.get("id")
            )
            self.db.add(config)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return {
            "id": config.id,
            "stage_name": config.stage_name,
            "default_hours": config.default_hours,
            "updated_at": config.updated_at
        }
    
    async def get_all_stage_times(self):
        result = await self.db.execute(select(StageTimeConfig))
        configs = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "stage_name": c.stage_name,
                "default_hours": c.default_hours,
                "updated_at": c.updated_at
            }
            for c in configs
        ]
    
    async def delete_stage_time(self, stage_name: str):
        result = await self.db.execute(
            select(StageTimeConfig).where(StageTimeConfig.stage_name == stage_name)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Stage time config not found")
        
        await self.db.delete(config)
        await self.db.commit()
        
        return {"message": f"Stage time for {stage_name} deleted successfully"}