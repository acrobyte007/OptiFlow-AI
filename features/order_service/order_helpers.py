from datetime import datetime, timedelta
from database.model import Order

STAGE_ORDER = ["PLACED", "VALIDATED", "INVENTORY_CHECK", "PROCESSING", "QC", "DISPATCHED", "DELIVERED"]

def calculate_progress(order: Order) -> float:
    try:
        current_index = STAGE_ORDER.index(order.status.value)
        total_stages = len(STAGE_ORDER) - 1
        return round((current_index / total_stages) * 100, 1)
    except ValueError:
        return 0.0

def calculate_time_remaining(order: Order) -> float:
    if not order.sla_deadline:
        return 0
    remaining = (order.sla_deadline - datetime.now()).total_seconds() / 3600
    return max(remaining, 0)

def calculate_risk_score(order: Order) -> float:
    if order.is_breached:
        return 1.0
    
    remaining = calculate_time_remaining(order)
    
    if remaining <= 0:
        return 1.0
    elif remaining < 12:
        return 0.9
    elif remaining < 24:
        return 0.7
    elif remaining < 48:
        return 0.5
    else:
        return 0.2

def calculate_estimated_arrival(order: Order) -> datetime:
    if order.status.value == "DELIVERED":
        return order.completed_at or datetime.now()
    
    progress = calculate_progress(order)
    
    if progress <= 0:
        return order.sla_deadline
    
    elapsed_seconds = (datetime.now() - order.created_at).total_seconds()
    estimated_total_seconds = elapsed_seconds / (progress / 100)
    remaining_seconds = estimated_total_seconds - elapsed_seconds
    
    if remaining_seconds < 0:
        return order.sla_deadline
    
    estimated = datetime.now() + timedelta(seconds=remaining_seconds)
    
    if estimated > order.sla_deadline:
        return order.sla_deadline
    
    return estimated