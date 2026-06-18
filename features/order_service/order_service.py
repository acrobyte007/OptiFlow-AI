from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException
from datetime import datetime, timedelta
from database.model import Order, Customer, Prescription, OrderLog, OrderLens, Lens, OrderStatus, QC, SLAConfig, StoreDelayConfig
from features.order_service.order_helpers import (
    calculate_progress,
    calculate_time_remaining,
    calculate_risk_score,
    calculate_estimated_arrival,
    STAGE_ORDER
)

class OrderService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_sla_config(self, lens_type: str) -> dict:
        result = await self.db.execute(
            select(SLAConfig).where(SLAConfig.lens_type == lens_type)
        )
        config = result.scalar_one_or_none()
        
        if config:
            return {
                "sla_hours": config.sla_hours,
                "complexity_factor": config.complexity_factor,
                "store_delay_hours": config.store_delay_hours
            }
        
        return {
            "sla_hours": 96,
            "complexity_factor": 1.0,
            "store_delay_hours": 0
        }
    
    async def _get_store_delay(self, store_location: str) -> int:
        result = await self.db.execute(
            select(StoreDelayConfig).where(StoreDelayConfig.store_location == store_location)
        )
        config = result.scalar_one_or_none()
        
        if config:
            return config.delay_hours
        
        return 0
    
    async def _calculate_sla_hours(self, lens_type: str, store_location: str, coating: str = None, frame: str = None) -> int:
        sla_config = await self._get_sla_config(lens_type)
        store_delay = await self._get_store_delay(store_location)
        
        hours = sla_config["sla_hours"]
        hours = int(hours * sla_config["complexity_factor"])
        hours += store_delay
        
        if coating:
            hours += 8
        
        if frame:
            hours += 4
        
        return hours
    
    async def create_order(self, request_data, current_user):
        customer_result = await self.db.execute(
            select(Customer).where(Customer.email == current_user.get("email"))
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            customer = Customer(
                name=current_user.get("name"),
                email=current_user.get("email"),
                phone=None
            )
            self.db.add(customer)
            await self.db.flush()
        
        sla_hours = await self._calculate_sla_hours(
            request_data.lens_type,
            request_data.store_location,
            request_data.coating,
            request_data.frame_model
        )
        sla_deadline = datetime.now() + timedelta(hours=sla_hours)
        
        order = Order(
            customer_id=customer.id,
            status=OrderStatus.PLACED,
            store_location=request_data.store_location,
            sla_hours=sla_hours,
            sla_deadline=sla_deadline,
            created_at=datetime.now(),
            is_breached=False
        )
        
        self.db.add(order)
        await self.db.flush()
        
        prescription = Prescription(
            order_id=order.id,
            sph=request_data.prescription.sph,
            cyl=request_data.prescription.cyl,
            axis=request_data.prescription.axis,
            add_power=request_data.prescription.add_power
        )
        self.db.add(prescription)
        
        log = OrderLog(
            order_id=order.id,
            status=OrderStatus.PLACED,
            performed_by_id=current_user.get("id"),
            delay_reason=None
        )
        self.db.add(log)
        
        lens_result = await self.db.execute(
            select(Lens).where(Lens.type == request_data.lens_type)
        )
        lens = lens_result.scalar_one_or_none()
        
        if lens:
            order_lens = OrderLens(
                order_id=order.id,
                lens_id=lens.id,
                power=request_data.prescription.sph
            )
            self.db.add(order_lens)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "status": order.status.value,
            "store_location": order.store_location,
            "sla_deadline": order.sla_deadline,
            "created_at": order.created_at,
            "message": "Order created successfully"
        }
    
    async def get_order_by_id(self, order_id: str, current_user):
        query = select(Order).where(Order.id == order_id)
        
        customer_result = await self.db.execute(
            select(Customer).where(Customer.email == current_user.get("email"))
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        if current_user.get("role") != "ADMIN":
            query = query.where(Order.customer_id == customer.id)
        
        order_result = await self.db.execute(query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return await self._build_order_response(order, customer)
    
    async def get_customer_orders(self, status: str = None, page: int = 1, limit: int = 20, current_user = None):
        customer_result = await self.db.execute(
            select(Customer).where(Customer.email == current_user.get("email"))
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        query = select(Order).where(Order.customer_id == customer.id)
        
        if status:
            query = query.where(Order.status == status)
        
        count_query = select(func.count()).select_from(Order).where(Order.customer_id == customer.id)
        if status:
            count_query = count_query.where(Order.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        order_list = []
        for order in orders:
            progress = calculate_progress(order)
            estimated_arrival = calculate_estimated_arrival(order)
            risk_score = calculate_risk_score(order)
            
            order_list.append({
                "id": order.id,
                "customer_id": order.customer_id,
                "customer_name": customer.name,
                "status": order.status.value,
                "store_location": order.store_location,
                "created_at": order.created_at,
                "sla_deadline": order.sla_deadline,
                "estimated_arrival": estimated_arrival,
                "progress_percentage": progress,
                "is_breached": order.is_breached,
                "risk_score": risk_score,
                "current_stage": order.status.value
            })
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "orders": order_list
        }
    
    async def get_all_orders_admin(self, status: str = None, store: str = None, customer_id: str = None, page: int = 1, limit: int = 20):
        query = select(Order)
        
        if status:
            query = query.where(Order.status == status)
        if store:
            query = query.where(Order.store_location == store)
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        
        count_query = select(func.count()).select_from(Order)
        if status:
            count_query = count_query.where(Order.status == status)
        if store:
            count_query = count_query.where(Order.store_location == store)
        if customer_id:
            count_query = count_query.where(Order.customer_id == customer_id)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        order_list = []
        for order in orders:
            customer_result = await self.db.execute(
                select(Customer).where(Customer.id == order.customer_id)
            )
            customer = customer_result.scalar_one_or_none()
            
            progress = calculate_progress(order)
            estimated_arrival = calculate_estimated_arrival(order)
            risk_score = calculate_risk_score(order)
            
            order_list.append({
                "id": order.id,
                "customer_id": order.customer_id,
                "customer_name": customer.name if customer else "Unknown",
                "status": order.status.value,
                "store_location": order.store_location,
                "created_at": order.created_at,
                "sla_deadline": order.sla_deadline,
                "estimated_arrival": estimated_arrival,
                "progress_percentage": progress,
                "is_breached": order.is_breached,
                "risk_score": risk_score,
                "current_stage": order.status.value
            })
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "orders": order_list
        }
    
    async def _build_order_response(self, order, customer):
        pres_result = await self.db.execute(
            select(Prescription).where(Prescription.order_id == order.id)
        )
        prescription = pres_result.scalar_one_or_none()
        
        lenses_result = await self.db.execute(
            select(OrderLens, Lens)
            .join(Lens, OrderLens.lens_id == Lens.id)
            .where(OrderLens.order_id == order.id)
        )
        order_lenses = lenses_result.all()
        
        logs_result = await self.db.execute(
            select(OrderLog).where(OrderLog.order_id == order.id)
        )
        logs = logs_result.scalars().all()
        
        qc_result = await self.db.execute(
            select(QC).where(QC.order_id == order.id)
        )
        qc_records = qc_result.scalars().all()
        
        progress = calculate_progress(order)
        time_remaining = calculate_time_remaining(order)
        risk_score = calculate_risk_score(order)
        estimated_arrival = calculate_estimated_arrival(order)
        
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": customer.name if customer else "Unknown",
            "status": order.status.value,
            "store_location": order.store_location,
            "created_at": order.created_at,
            "sla_deadline": order.sla_deadline,
            "estimated_arrival": estimated_arrival,
            "time_remaining_hours": time_remaining,
            "progress_percentage": progress,
            "is_breached": order.is_breached,
            "risk_score": risk_score,
            "current_stage": order.status.value,
            "prescription": {
                "sph": prescription.sph,
                "cyl": prescription.cyl,
                "axis": prescription.axis,
                "add_power": prescription.add_power
            } if prescription else None,
            "order_lenses": [
                {
                    "lens_type": lens.type,
                    "lens_index": lens.index,
                    "coating": lens.coating,
                    "power": ol.power
                }
                for ol, lens in order_lenses
            ],
            "logs": [
                {
                    "status": log.status.value,
                    "timestamp": log.timestamp,
                    "delay_reason": log.delay_reason
                }
                for log in logs
            ],
            "qc_records": [
                {
                    "result": qc.result.value,
                    "reason": qc.reason,
                    "timestamp": qc.timestamp
                }
                for qc in qc_records
            ]
        }