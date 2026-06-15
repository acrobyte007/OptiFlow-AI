from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey,
    DateTime, Text, Enum, Boolean, Index
)
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid
from datetime import datetime, timedelta

Base = declarative_base()

# ------------------------
# Utils
# ------------------------
def generate_uuid():
    return str(uuid.uuid4())

# ------------------------
# Enums
# ------------------------
class OrderStatus(enum.Enum):
    PLACED = "PLACED"
    VALIDATED = "VALIDATED"
    INVENTORY_CHECK = "INVENTORY_CHECK"
    PROCESSING = "PROCESSING"
    QC = "QC"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"


class QCResult(enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class InventorySource(enum.Enum):
    IN_HOUSE = "IN_HOUSE"
    VENDOR = "VENDOR"


class AlertChannel(enum.Enum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class AlertStatus(enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"


# ------------------------
# Models
# ------------------------

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"))

    status = Column(Enum(OrderStatus), default=OrderStatus.PLACED)

    # SLA + TAT
    sla_hours = Column(Integer)
    sla_deadline = Column(DateTime)
    predicted_tat = Column(DateTime)

    # Tracking timestamps (important for AI)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Dashboard filters
    store_location = Column(String)

    # Breach flag
    is_breached = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="orders")
    prescription = relationship("Prescription", uselist=False, back_populates="order")
    logs = relationship("OrderLog", back_populates="order")
    qc_records = relationship("QC", back_populates="order")
    shipment = relationship("Shipment", uselist=False, back_populates="order")
    alerts = relationship("Alert", back_populates="order")
    order_lenses = relationship("OrderLens", back_populates="order")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))

    sph = Column(Float)
    cyl = Column(Float)
    axis = Column(Integer)
    add_power = Column(Float)

    order = relationship("Order", back_populates="prescription")


class Lens(Base):
    __tablename__ = "lenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String)
    index = Column(Float)
    coating = Column(String)

    inventory_items = relationship("Inventory", back_populates="lens")
    order_lenses = relationship("OrderLens", back_populates="lens")


class OrderLens(Base):
    __tablename__ = "order_lens"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    lens_id = Column(String, ForeignKey("lenses.id"))

    power = Column(Float)

    order = relationship("Order", back_populates="order_lenses")
    lens = relationship("Lens", back_populates="order_lenses")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String, primary_key=True, default=generate_uuid)
    lens_id = Column(String, ForeignKey("lenses.id"))

    power = Column(Float)
    quantity = Column(Integer)
    location = Column(String)

    # NEW: inventory intelligence
    source = Column(Enum(InventorySource))  # IN_HOUSE / VENDOR
    lead_time_hours = Column(Integer)  # vendor delay

    lens = relationship("Lens", back_populates="inventory_items")


class OrderLog(Base):
    __tablename__ = "order_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))

    status = Column(Enum(OrderStatus))
    timestamp = Column(DateTime, default=datetime.now)

    updated_by = Column(String)
    delay_reason = Column(Text)

    order = relationship("Order", back_populates="logs")


class QC(Base):
    __tablename__ = "qc"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))

    result = Column(Enum(QCResult))
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    order = relationship("Order", back_populates="qc_records")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))

    courier = Column(String)
    tracking_id = Column(String)

    dispatched_at = Column(DateTime)
    delivered_at = Column(DateTime)

    order = relationship("Order", back_populates="shipment")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))

    type = Column(String)  # SLA_BREACH / WARNING
    message = Column(Text)

    # NEW: channel + delivery tracking
    channel = Column(Enum(AlertChannel))  # EMAIL / WHATSAPP
    status = Column(Enum(AlertStatus))    # SENT / FAILED

    sent_at = Column(DateTime, default=datetime.now)

    order = relationship("Order", back_populates="alerts")


# ------------------------
# Indexes (Performance)
# ------------------------

Index("idx_order_status", Order.status)
Index("idx_order_store", Order.store_location)
Index("idx_inventory_lookup", Inventory.lens_id, Inventory.power)
Index("idx_sla_deadline", Order.sla_deadline)