from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey,
    DateTime, Text, Enum, Boolean, Index
)
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid
from datetime import datetime

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

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

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    STORE_MANAGER = "STORE_MANAGER"
    QC_INSPECTOR = "QC_INSPECTOR"
    WAREHOUSE = "WAREHOUSE"
    SUPPORT = "SUPPORT"
    CUSTOMER = "CUSTOMER"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    store_location = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    order_logs = relationship("OrderLog", back_populates="performed_by")
    qc_records = relationship("QC", back_populates="performed_by")

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
    sla_hours = Column(Integer)
    sla_deadline = Column(DateTime)
    predicted_tat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    store_location = Column(String)
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
    source = Column(Enum(InventorySource))
    lead_time_hours = Column(Integer)

    lens = relationship("Lens", back_populates="inventory_items")

class OrderLog(Base):
    __tablename__ = "order_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    status = Column(Enum(OrderStatus))
    timestamp = Column(DateTime, default=datetime.now)
    performed_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    delay_reason = Column(Text)

    order = relationship("Order", back_populates="logs")
    performed_by = relationship("User", back_populates="order_logs")

class QC(Base):
    __tablename__ = "qc"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    result = Column(Enum(QCResult))
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    performed_by_id = Column(String, ForeignKey("users.id"), nullable=True)

    order = relationship("Order", back_populates="qc_records")
    performed_by = relationship("User", back_populates="qc_records")

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
    type = Column(String)
    message = Column(Text)
    channel = Column(Enum(AlertChannel))
    status = Column(Enum(AlertStatus))
    sent_at = Column(DateTime, default=datetime.now)

    order = relationship("Order", back_populates="alerts")


class SLAConfig(Base):
    __tablename__ = "sla_config"

    id = Column(String, primary_key=True, default=generate_uuid)
    lens_type = Column(String, unique=True, nullable=False)
    sla_hours = Column(Integer, nullable=False)
    complexity_factor = Column(Float, default=1.0)
    store_delay_hours = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(String, nullable=True)  # Admin user ID

class StoreDelayConfig(Base):
    __tablename__ = "store_delay_config"

    id = Column(String, primary_key=True, default=generate_uuid)
    store_location = Column(String, unique=True, nullable=False)
    delay_hours = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(String, nullable=True)

class StageTimeConfig(Base):
    __tablename__ = "stage_time_config"

    id = Column(String, primary_key=True, default=generate_uuid)
    stage_name = Column(String, unique=True, nullable=False)
    default_hours = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(String, nullable=True)

Index("idx_order_status", Order.status)
Index("idx_order_store", Order.store_location)
Index("idx_inventory_lookup", Inventory.lens_id, Inventory.power)
Index("idx_sla_deadline", Order.sla_deadline)
Index("idx_user_email", User.email)
Index("idx_user_role", User.role)